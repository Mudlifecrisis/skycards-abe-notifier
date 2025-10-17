#!/usr/bin/env python3
"""
Analyze large aircraft database with proper CSV handling
"""
import csv
import json
import os
from datetime import datetime

# Increase CSV field size limit
csv.field_size_limit(1000000)

def analyze_database_safely(csv_file):
    """Safely analyze the user's aircraft database"""
    
    print("Analyzing Large Aircraft Database")
    print("=" * 50)
    print(f"File: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        return None
    
    file_size = os.path.getsize(csv_file)
    print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first line manually to analyze header
            first_line = f.readline().strip()
            print(f"Raw header: {first_line[:200]}...")
            
            # Parse CSV properly
            f.seek(0)
            try:
                csv_reader = csv.reader(f, quotechar="'")
                headers = next(csv_reader)
                
                print(f"Columns found: {len(headers)}")
                
                # Find key column indices
                key_columns = {}
                for i, header in enumerate(headers):
                    clean_header = header.strip("'\"")
                    if clean_header in ['icao24', 'typecode', 'registration', 'model', 'manufacturerName', 'operator']:
                        key_columns[clean_header] = i
                        print(f"  {clean_header}: Column {i}")
                
                if 'icao24' not in key_columns or 'typecode' not in key_columns:
                    print("Error: Missing required columns (icao24 or typecode)")
                    return None
                
                # Process data rows
                total_records = 0
                valid_records = 0
                rare_aircraft = {'AB18': [], 'VUT1': [], 'C17': [], 'F16': [], 'A10': []}
                
                print(f"\nProcessing records...")
                
                for row_num, row in enumerate(csv_reader):
                    total_records += 1
                    
                    if len(row) <= max(key_columns.values()):
                        continue  # Skip incomplete rows
                    
                    try:
                        icao24 = row[key_columns['icao24']].strip("'\"").lower()
                        typecode = row[key_columns['typecode']].strip("'\"").upper()
                        
                        if icao24 and typecode and len(icao24) == 6:  # Valid ICAO24 format
                            valid_records += 1
                            
                            # Check for rare aircraft
                            if typecode in rare_aircraft:
                                registration = row[key_columns.get('registration', 0)].strip("'\"") if 'registration' in key_columns else ''
                                model = row[key_columns.get('model', 0)].strip("'\"") if 'model' in key_columns else ''
                                
                                rare_aircraft[typecode].append({
                                    'icao24': icao24,
                                    'registration': registration,
                                    'model': model
                                })
                            
                            # Show sample data
                            if valid_records <= 10:
                                registration = row[key_columns.get('registration', 0)].strip("'\"") if 'registration' in key_columns else ''
                                model = row[key_columns.get('model', 0)].strip("'\"") if 'model' in key_columns else ''
                                print(f"  Record {valid_records}: {icao24} -> {typecode} ({registration}) {model}")
                    
                    except Exception as e:
                        pass  # Skip problematic rows
                    
                    # Progress updates
                    if total_records % 100000 == 0:
                        print(f"    Processed {total_records:,} rows, found {valid_records:,} valid aircraft...")
                
                print(f"\nAnalysis Results:")
                print(f"  Total rows processed: {total_records:,}")
                print(f"  Valid aircraft records: {valid_records:,}")
                print(f"  Data quality: {valid_records/total_records*100:.1f}%")
                
                print(f"\nRare Aircraft Found:")
                total_rare = 0
                for aircraft_type, aircraft_list in rare_aircraft.items():
                    count = len(aircraft_list)
                    total_rare += count
                    if count > 0:
                        print(f"  {aircraft_type}: {count} aircraft")
                        # Show examples
                        for aircraft in aircraft_list[:3]:
                            print(f"    {aircraft['icao24']}: {aircraft['registration']} - {aircraft['model']}")
                        if count > 3:
                            print(f"    ... and {count - 3} more")
                    else:
                        print(f"  {aircraft_type}: NOT FOUND")
                
                return {
                    'total_records': total_records,
                    'valid_records': valid_records,
                    'rare_aircraft': rare_aircraft,
                    'total_rare': total_rare
                }
                
            except Exception as csv_error:
                print(f"CSV parsing error: {csv_error}")
                return None
                
    except Exception as e:
        print(f"Error analyzing database: {e}")
        return None

def compare_with_old_database(new_analysis):
    """Compare new database with the old one"""
    
    print(f"\n" + "=" * 60)
    print("DATABASE COMPARISON")
    print("=" * 60)
    
    old_db_file = "aircraft_data/aircraft_database.json"
    
    if os.path.exists(old_db_file):
        try:
            with open(old_db_file, 'r') as f:
                old_data = json.load(f)
            
            print(f"OLD DATABASE (OpenSky download):")
            print(f"  Total aircraft: {len(old_data):,}")
            
            # Count rare aircraft in old database
            old_rare_count = {}
            rare_types = {'AB18', 'VUT1', 'C17', 'F16', 'A10'}
            for icao24, info in old_data.items():
                aircraft_type = info.get('type', '')
                if aircraft_type in rare_types:
                    old_rare_count[aircraft_type] = old_rare_count.get(aircraft_type, 0) + 1
            
            for aircraft_type in rare_types:
                old_count = old_rare_count.get(aircraft_type, 0)
                new_count = len(new_analysis['rare_aircraft'].get(aircraft_type, []))
                print(f"  {aircraft_type}: {old_count} → {new_count} ({new_count - old_count:+d})")
            
            print(f"\nNEW DATABASE (Your 2025-08 file):")
            print(f"  Total aircraft: {new_analysis['valid_records']:,}")
            print(f"  Quality improvement: {new_analysis['valid_records'] - len(old_data):+,} more aircraft")
            
            total_old_rare = sum(old_rare_count.values())
            total_new_rare = new_analysis['total_rare']
            print(f"  Rare aircraft: {total_old_rare} → {total_new_rare} ({total_new_rare - total_old_rare:+d})")
            
            if total_new_rare > total_old_rare:
                print(f"\n✅ NEW DATABASE IS BETTER! More complete rare aircraft data.")
            else:
                print(f"\n⚠️  Old database had more rare aircraft. Check data quality.")
                
        except Exception as e:
            print(f"Could not load old database: {e}")
    else:
        print("No old database found for comparison")

def main():
    """Main function"""
    
    csv_file = r"C:\Projects\GitHub-Repos\Skycards-Project\aircraft_data\aircraft-database-complete-2025-08.csv"
    
    # Analyze the database
    analysis = analyze_database_safely(csv_file)
    
    if analysis:
        # Compare with old database
        compare_with_old_database(analysis)
        
        print(f"\n" + "=" * 60)
        print("RECOMMENDATION")
        print("=" * 60)
        
        if analysis['total_rare'] > 0:
            print(f"✅ Your 2025-08 database contains rare aircraft!")
            print(f"✅ Should use this newer database for monitoring")
            print(f"✅ Ready to convert to optimized JSON format")
        else:
            print(f"⚠️  No rare aircraft found in new database")
            print(f"⚠️  May need to investigate data format")

if __name__ == "__main__":
    main()