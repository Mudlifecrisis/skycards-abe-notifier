#!/usr/bin/env python3
"""
Download OpenSky aircraft database and build ICAO24 -> aircraft type lookup
"""
import asyncio
import aiohttp
import csv
from io import StringIO

async def download_opensky_aircraft_db():
    """Download and analyze OpenSky's complete aircraft database"""
    
    print("Downloading OpenSky Aircraft Database")
    print("=" * 50)
    
    # OpenSky aircraft database URL
    db_url = "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(db_url) as response:
                print(f"Download Status: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"Database size: {len(content)} characters")
                    
                    # Parse CSV
                    csv_reader = csv.DictReader(StringIO(content))
                    records = list(csv_reader)
                    print(f"Total aircraft records: {len(records)}")
                    
                    # Build ICAO24 -> aircraft type lookup
                    icao24_to_type = {}
                    type_counts = {}
                    
                    for record in records:
                        icao24 = record.get('icao24', '').lower().strip()
                        typecode = record.get('typecode', '').strip()
                        
                        if icao24 and typecode:
                            icao24_to_type[icao24] = typecode
                            type_counts[typecode] = type_counts.get(typecode, 0) + 1
                    
                    print(f"Aircraft with type codes: {len(icao24_to_type)}")
                    print(f"Unique aircraft types: {len(type_counts)}")
                    
                    # Search for AB18 specifically
                    ab18_aircraft = [icao24 for icao24, typecode in icao24_to_type.items() if typecode == 'AB18']
                    print(f"\nAB18 aircraft found: {len(ab18_aircraft)}")
                    
                    if ab18_aircraft:
                        print("AB18 ICAO24 codes:")
                        for icao24 in ab18_aircraft[:10]:  # Show first 10
                            print(f"  {icao24}")
                    
                    # Show all aircraft types containing "AB"
                    ab_types = {t: count for t, count in type_counts.items() if 'AB' in t.upper()}
                    print(f"\nAircraft types containing 'AB': {len(ab_types)}")
                    for aircraft_type, count in sorted(ab_types.items()):
                        print(f"  {aircraft_type}: {count} aircraft")
                    
                    # Search for rare aircraft types (low counts)
                    rare_types = [(t, count) for t, count in type_counts.items() if count <= 5]
                    rare_types.sort(key=lambda x: x[1])
                    
                    print(f"\nRarest aircraft types (5 or fewer):")
                    for aircraft_type, count in rare_types[:20]:
                        print(f"  {aircraft_type}: {count} aircraft")
                    
                    # Test the lookup system
                    print(f"\n--- Testing Lookup System ---")
                    
                    # Test with known C-17 ICAO24
                    test_icao24 = "ae117c"  # RCH4231 from our previous tests
                    if test_icao24 in icao24_to_type:
                        aircraft_type = icao24_to_type[test_icao24]
                        print(f"Test lookup - {test_icao24}: {aircraft_type}")
                    else:
                        print(f"Test lookup - {test_icao24}: NOT FOUND")
                    
                    # Show the lookup table structure for monitoring
                    print(f"\nLookup table ready: {len(icao24_to_type)} mappings")
                    print("System can now monitor live feed and identify aircraft types instantly")
                    
                    return icao24_to_type
                    
    except Exception as e:
        print(f"Error downloading aircraft database: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(download_opensky_aircraft_db())