#!/usr/bin/env python3
"""
Convert user's 2025-08 database to optimized production format
"""
import csv
import json
import os
from datetime import datetime

# Increase CSV field size limit
csv.field_size_limit(1000000)

def convert_to_production_format():
    """Convert the user's CSV to optimized JSON for production monitoring"""
    
    print("Converting to Production Database Format")
    print("=" * 60)
    
    input_file = r"C:\Projects\GitHub-Repos\Skycards-Project\aircraft_data\aircraft-database-complete-2025-08.csv"
    output_file = "aircraft_data/production_aircraft_database.json"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return False
    
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    try:
        # Production database structure
        aircraft_db = {}
        rare_aircraft_db = {}
        user_target_aircraft = {}  # Specifically your rare types
        
        # Your target rare aircraft types
        target_types = {'AB18', 'VUT1'}  # Focus on YOUR specific rare aircraft
        all_rare_types = {'AB18', 'VUT1', 'C17', 'F16', 'A10'}  # All rare types for monitoring
        
        processed_count = 0
        valid_count = 0
        
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            csv_reader = csv.reader(f, quotechar="'")
            headers = next(csv_reader)
            
            # Find column indices
            col_indices = {}
            for i, header in enumerate(headers):
                clean_header = header.strip("'\"")
                if clean_header in ['icao24', 'typecode', 'registration', 'model', 'manufacturerName', 'operator']:
                    col_indices[clean_header] = i
            
            print(f"Processing aircraft records...")
            
            for row in csv_reader:
                processed_count += 1
                
                if len(row) <= max(col_indices.values()):
                    continue
                
                try:
                    icao24 = row[col_indices['icao24']].strip("'\"").lower()
                    typecode = row[col_indices['typecode']].strip("'\"").upper()
                    
                    if icao24 and typecode and len(icao24) == 6:
                        registration = row[col_indices.get('registration', 0)].strip("'\"") if 'registration' in col_indices else ''
                        model = row[col_indices.get('model', 0)].strip("'\"") if 'model' in col_indices else ''
                        manufacturer = row[col_indices.get('manufacturerName', 0)].strip("'\"") if 'manufacturerName' in col_indices else ''
                        operator = row[col_indices.get('operator', 0)].strip("'\"") if 'operator' in col_indices else ''
                        
                        # Create aircraft record
                        aircraft_info = {
                            'type': typecode,
                            'registration': registration,
                            'model': model,
                            'manufacturer': manufacturer,
                            'operator': operator
                        }
                        
                        # Store in main database
                        aircraft_db[icao24] = aircraft_info
                        valid_count += 1
                        
                        # Store rare aircraft separately for quick access
                        if typecode in all_rare_types:
                            rare_aircraft_db[icao24] = aircraft_info
                            
                            # Store your specific target aircraft
                            if typecode in target_types:
                                user_target_aircraft[icao24] = aircraft_info
                                print(f"  TARGET AIRCRAFT: {icao24} -> {typecode} ({registration}) {model}")
                
                except Exception:
                    continue
                
                # Progress updates
                if processed_count % 100000 == 0:
                    print(f"    Processed {processed_count:,} rows, {valid_count:,} valid aircraft...")
        
        print(f"\nConversion Results:")
        print(f"  Processed rows: {processed_count:,}")
        print(f"  Valid aircraft: {valid_count:,}")
        print(f"  All rare aircraft: {len(rare_aircraft_db)}")
        print(f"  YOUR target aircraft: {len(user_target_aircraft)}")
        
        # Create production database structure
        production_db = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'source': 'aircraft-database-complete-2025-08.csv',
                'total_aircraft': valid_count,
                'rare_aircraft_count': len(rare_aircraft_db),
                'user_target_count': len(user_target_aircraft),
                'target_types': list(target_types),
                'all_rare_types': list(all_rare_types)
            },
            'aircraft': aircraft_db,
            'rare_aircraft': rare_aircraft_db,
            'user_targets': user_target_aircraft
        }
        
        # Save production database
        print(f"\nSaving production database...")
        with open(output_file, 'w') as f:
            json.dump(production_db, f, indent=2)
        
        output_size = os.path.getsize(output_file)
        print(f"Production database saved!")
        print(f"  File: {output_file}")
        print(f"  Size: {output_size:,} bytes ({output_size / 1024 / 1024:.1f} MB)")
        
        # Show your specific aircraft details
        print(f"\nYOUR TARGET AIRCRAFT READY FOR MONITORING:")
        print("=" * 50)
        
        target_by_type = {}
        for icao24, info in user_target_aircraft.items():
            aircraft_type = info['type']
            if aircraft_type not in target_by_type:
                target_by_type[aircraft_type] = []
            target_by_type[aircraft_type].append((icao24, info))
        
        for aircraft_type, aircraft_list in target_by_type.items():
            type_name = {'AB18': 'Aero Boero AB-180', 'VUT1': 'Evektor Cobra'}[aircraft_type]
            print(f"\n{aircraft_type} ({type_name}): {len(aircraft_list)} aircraft")
            for icao24, info in aircraft_list:
                print(f"  {icao24}: {info['registration']} - {info['model']}")
        
        return True
        
    except Exception as e:
        print(f"Error converting database: {e}")
        return False

def create_monitoring_config():
    """Create configuration file for the monitoring system"""
    
    config = {
        'monitoring': {
            'database_file': 'aircraft_data/production_aircraft_database.json',
            'check_interval_seconds': 15,
            'api_timeout_seconds': 30,
            'max_consecutive_errors': 5
        },
        'target_aircraft': {
            'AB18': {
                'name': 'Aero Boero AB-180',
                'priority': 'HIGH',
                'notify': True,
                'sound_alert': True
            },
            'VUT1': {
                'name': 'Evektor Cobra', 
                'priority': 'HIGH',
                'notify': True,
                'sound_alert': True
            }
        },
        'other_rare_aircraft': {
            'C17': {
                'name': 'Boeing C-17 Globemaster',
                'priority': 'MEDIUM',
                'notify': True,
                'sound_alert': False
            },
            'F16': {
                'name': 'F-16 Fighting Falcon',
                'priority': 'MEDIUM', 
                'notify': True,
                'sound_alert': False
            },
            'A10': {
                'name': 'A-10 Thunderbolt II',
                'priority': 'MEDIUM',
                'notify': True,
                'sound_alert': False
            }
        },
        'notifications': {
            'desktop_notifications': True,
            'sound_alerts': True,
            'log_to_file': True,
            'log_file': 'aircraft_data/detection_log.txt'
        }
    }
    
    config_file = "aircraft_data/monitoring_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nMonitoring configuration created: {config_file}")
    return config

def main():
    """Main conversion function"""
    
    # Convert database
    success = convert_to_production_format()
    
    if success:
        # Create monitoring config
        config = create_monitoring_config()
        
        print(f"\n" + "=" * 60)
        print("PRODUCTION DATABASE READY!")
        print("=" * 60)
        print("✓ Database converted and optimized")
        print("✓ Your target aircraft identified")
        print("✓ Monitoring configuration created")
        print("✓ Ready to build production monitoring system")
        
        print(f"\nNEXT: Build the 24/7 monitoring service!")
    else:
        print(f"\nConversion failed. Check errors above.")

if __name__ == "__main__":
    main()