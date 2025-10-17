#!/usr/bin/env python3
"""
Analyze the user's more recent aircraft database and convert to optimized format
"""
import csv
import json
import os
from datetime import datetime

def analyze_database(csv_file):
    """Analyze the user's aircraft database"""
    
    print("Analyzing Aircraft Database")
    print("=" * 50)
    print(f"File: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        return None
    
    file_size = os.path.getsize(csv_file)
    print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
    
    try:
        # Analyze CSV structure
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Read header
            header_line = f.readline().strip()
            print(f"Header: {header_line[:100]}...")
            
            # Parse header
            headers = [h.strip("'\"") for h in header_line.split(',')]
            print(f"Columns: {len(headers)}")
            
            # Show key columns
            key_columns = ['icao24', 'typecode', 'registration', 'model', 'manufacturerName', 'operator']
            for col in key_columns:
                if col in headers:
                    idx = headers.index(col)
                    print(f"  {col}: Column {idx}")
                else:
                    print(f"  {col}: NOT FOUND")
            
            # Count total records
            f.seek(0)  # Reset to beginning
            csv_reader = csv.DictReader(f)
            
            total_records = 0
            records_with_type = 0
            rare_aircraft = {'AB18': 0, 'VUT1': 0, 'C17': 0, 'F16': 0, 'A10': 0}
            
            # Sample first few records
            print(f"\nSample records:")
            for i, record in enumerate(csv_reader):
                total_records += 1
                
                if i < 5:  # Show first 5 records
                    icao24 = record.get('icao24', '').strip("'\"")
                    typecode = record.get('typecode', '').strip("'\"") 
                    registration = record.get('registration', '').strip("'\"")
                    model = record.get('model', '').strip("'\"")
                    
                    print(f"  Record {i+1}:")
                    print(f"    ICAO24: {icao24}")
                    print(f"    Type: {typecode}")
                    print(f"    Registration: {registration}")
                    print(f"    Model: {model}")
                
                # Count records with typecode
                typecode = record.get('typecode', '').strip("'\"")
                if typecode and typecode != '':
                    records_with_type += 1
                    
                    # Count rare aircraft
                    if typecode in rare_aircraft:
                        rare_aircraft[typecode] += 1
                
                # Progress indicator for large files
                if total_records % 50000 == 0:
                    print(f"  Processed {total_records:,} records...")
            
            print(f"\nDatabase Analysis Results:")
            print(f"  Total records: {total_records:,}")
            print(f"  Records with typecode: {records_with_type:,}")
            print(f"  Coverage: {records_with_type/total_records*100:.1f}%")
            
            print(f"\nRare Aircraft Found:")
            for aircraft_type, count in rare_aircraft.items():
                if count > 0:
                    print(f"  {aircraft_type}: {count} aircraft")
                else:
                    print(f"  {aircraft_type}: NOT FOUND")
            
            return {
                'total_records': total_records,
                'records_with_type': records_with_type,
                'rare_aircraft': rare_aircraft,
                'headers': headers
            }
            
    except Exception as e:
        print(f"Error analyzing database: {e}")
        return None

def convert_to_optimized_format(csv_file, output_file):
    """Convert CSV to optimized JSON format for monitoring"""
    
    print(f"\nConverting to optimized format...")
    print(f"Input: {csv_file}")
    print(f"Output: {output_file}")
    
    try:
        aircraft_db = {}
        rare_aircraft_db = {}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            
            processed = 0
            
            for record in csv_reader:
                icao24 = record.get('icao24', '').strip("'\"").lower()
                typecode = record.get('typecode', '').strip("'\"").upper()
                
                if icao24 and typecode:
                    # Store essential info only
                    aircraft_info = {
                        'type': typecode,
                        'registration': record.get('registration', '').strip("'\""),
                        'model': record.get('model', '').strip("'\""),
                        'manufacturer': record.get('manufacturerName', '').strip("'\""),
                        'operator': record.get('operator', '').strip("'\"")
                    }
                    
                    aircraft_db[icao24] = aircraft_info
                    
                    # Track rare aircraft separately for quick access
                    rare_types = {'AB18', 'VUT1', 'C17', 'F16', 'A10'}
                    if typecode in rare_types:
                        rare_aircraft_db[icao24] = aircraft_info
                    
                    processed += 1
                    
                    if processed % 50000 == 0:
                        print(f"  Converted {processed:,} records...")
        
        # Save optimized database
        database_data = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'source_file': os.path.basename(csv_file),
                'total_aircraft': len(aircraft_db),
                'rare_aircraft': len(rare_aircraft_db)
            },
            'aircraft': aircraft_db,
            'rare_aircraft': rare_aircraft_db
        }
        
        with open(output_file, 'w') as f:
            json.dump(database_data, f, indent=2)
        
        output_size = os.path.getsize(output_file)
        print(f"\nConversion complete!")
        print(f"  Aircraft processed: {processed:,}")
        print(f"  Output size: {output_size:,} bytes ({output_size / 1024 / 1024:.1f} MB)")
        print(f"  Rare aircraft: {len(rare_aircraft_db)}")
        
        return database_data
        
    except Exception as e:
        print(f"Error converting database: {e}")
        return None

def compare_databases():
    """Compare the new database with what we downloaded earlier"""
    
    print(f"\n" + "=" * 60)
    print("DATABASE COMPARISON")
    print("=" * 60)
    
    old_db_file = "aircraft_data/aircraft_database.json"
    
    if os.path.exists(old_db_file):
        try:
            with open(old_db_file, 'r') as f:
                old_data = json.load(f)
            
            print(f"OLD DATABASE (downloaded from OpenSky):")
            print(f"  Aircraft count: {len(old_data):,}")
            
            # Count rare aircraft in old database
            old_rare_count = {}
            rare_types = {'AB18', 'VUT1', 'C17', 'F16', 'A10'}
            for icao24, info in old_data.items():
                aircraft_type = info.get('type', '')
                if aircraft_type in rare_types:
                    old_rare_count[aircraft_type] = old_rare_count.get(aircraft_type, 0) + 1
            
            for aircraft_type in rare_types:
                count = old_rare_count.get(aircraft_type, 0)
                print(f"  {aircraft_type}: {count}")
                
        except Exception as e:
            print(f"Could not load old database: {e}")
    else:
        print("No old database found for comparison")

def main():
    """Main function"""
    
    # File paths
    user_csv = r"C:\Projects\GitHub-Repos\Skycards-Project\aircraft_data\aircraft-database-complete-2025-08.csv"
    optimized_json = "aircraft_data/aircraft_database_2025_08.json"
    
    # Analyze the user's database
    analysis = analyze_database(user_csv)
    
    if analysis:
        # Convert to optimized format
        converted_data = convert_to_optimized_format(user_csv, optimized_json)
        
        if converted_data:
            # Compare with old database
            compare_databases()
            
            # Show rare aircraft details
            print(f"\nYOUR RARE AIRCRAFT (from new database):")
            print("=" * 50)
            
            rare_aircraft = converted_data['rare_aircraft']
            
            # Group by type
            by_type = {}
            for icao24, info in rare_aircraft.items():
                aircraft_type = info['type']
                if aircraft_type not in by_type:
                    by_type[aircraft_type] = []
                by_type[aircraft_type].append((icao24, info))
            
            for aircraft_type, aircraft_list in by_type.items():
                print(f"\n{aircraft_type}: {len(aircraft_list)} aircraft")
                for icao24, info in aircraft_list[:5]:  # Show first 5
                    print(f"  {icao24}: {info['registration']} - {info['model']}")
                if len(aircraft_list) > 5:
                    print(f"  ... and {len(aircraft_list) - 5} more")

if __name__ == "__main__":
    main()