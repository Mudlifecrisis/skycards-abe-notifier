#!/usr/bin/env python3
"""
Test the plane-alert-db repository for aircraft type mapping
"""
import asyncio
import aiohttp
import csv
from io import StringIO

async def test_plane_alert_database():
    """Test plane-alert-db for our aircraft search needs"""
    
    print("Testing plane-alert-db for Aircraft Type Mapping")
    print("=" * 60)
    
    # Test the main database file
    csv_url = "https://raw.githubusercontent.com/sdr-enthusiasts/plane-alert-db/main/plane-alert-db.csv"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(csv_url) as response:
                print(f"Download Status: {response.status}")
                
                if response.status == 200:
                    # Download full file to analyze
                    content = await response.text()
                    
                    print(f"File size: {len(content)} characters")
                    
                    # Parse CSV
                    csv_reader = csv.DictReader(StringIO(content))
                    
                    # Count records and analyze
                    records = list(csv_reader)
                    print(f"Total aircraft records: {len(records)}")
                    
                    # Look for our test aircraft types
                    test_types = {
                        'C17': 'Globemaster',
                        'A10': 'Warthog', 
                        'F16': 'Viper',
                        'F15': 'Eagle',
                        'C135': 'Stratolifter',
                        'AB18': 'Aero Boero',
                        'VUT1': 'Evektor Cobra'
                    }
                    
                    found_types = {}
                    aircraft_by_type = {}
                    
                    for record in records:
                        icao24 = record.get('$ICAO', '').lower()
                        icao_type = record.get('$ICAO Type', '').upper()
                        full_name = record.get('$Type', '')
                        operator = record.get('$Operator', '')
                        
                        if icao_type:
                            if icao_type not in aircraft_by_type:
                                aircraft_by_type[icao_type] = []
                            
                            aircraft_by_type[icao_type].append({
                                'icao24': icao24,
                                'name': full_name,
                                'operator': operator
                            })
                            
                            # Check if this matches our test types
                            if icao_type in test_types:
                                if icao_type not in found_types:
                                    found_types[icao_type] = []
                                found_types[icao_type].append({
                                    'icao24': icao24,
                                    'name': full_name,
                                    'operator': operator
                                })
                    
                    print(f"\nUnique aircraft types: {len(aircraft_by_type)}")
                    
                    # Show our test results
                    print(f"\nTest Aircraft Types Found:")
                    for test_type, friendly_name in test_types.items():
                        if test_type in found_types:
                            count = len(found_types[test_type])
                            print(f"  [FOUND] {test_type} ({friendly_name}): {count} aircraft")
                            
                            # Show examples
                            for example in found_types[test_type][:3]:
                                print(f"    - {example['icao24']}: {example['name']} ({example['operator']})")
                        else:
                            print(f"  [NOT FOUND] {test_type} ({friendly_name}): Not found")
                    
                    # Show top aircraft types by count
                    type_counts = [(t, len(aircraft)) for t, aircraft in aircraft_by_type.items()]
                    type_counts.sort(key=lambda x: x[1], reverse=True)
                    
                    print(f"\nTop 10 Aircraft Types by Count:")
                    for aircraft_type, count in type_counts[:10]:
                        print(f"  {aircraft_type}: {count} aircraft")
                    
                    # Test building a search index
                    print(f"\nBuilding Search Index...")
                    
                    # Create reverse mapping: ICAO Type → ICAO24 list
                    type_to_icao24 = {}
                    for record in records:
                        icao24 = record.get('$ICAO', '').lower()
                        icao_type = record.get('$ICAO Type', '').upper()
                        
                        if icao24 and icao_type:
                            if icao_type not in type_to_icao24:
                                type_to_icao24[icao_type] = []
                            type_to_icao24[icao_type].append(icao24)
                    
                    # Test search functionality
                    print(f"\nTesting Search Functionality:")
                    
                    # Simulate user searching for "globemaster"
                    search_term = "globemaster"
                    target_type = "C17"  # Our alias mapping
                    
                    if target_type in type_to_icao24:
                        matching_icao24s = type_to_icao24[target_type]
                        print(f"  Search '{search_term}' -> Type '{target_type}' -> {len(matching_icao24s)} aircraft")
                        print(f"  ICAO24 codes: {matching_icao24s[:5]}...")  # Show first 5
                        
                        print(f"\n[SUCCESS] We can find all {target_type} aircraft without API calls!")
                    else:
                        print(f"  Search '{search_term}' -> Type '{target_type}' -> No aircraft found")
                
    except Exception as e:
        print(f"Error testing plane-alert-db: {e}")

if __name__ == "__main__":
    asyncio.run(test_plane_alert_database())