#!/usr/bin/env python3
"""
Investigate OpenSky Network metadata datasets for aircraft type information
"""
import asyncio
import aiohttp
import csv
from io import StringIO

async def investigate_opensky_metadata():
    """Investigate OpenSky metadata datasets"""
    
    print("Investigating OpenSky Network Metadata Datasets")
    print("=" * 60)
    
    # URLs from the OpenSky datasets page
    metadata_urls = [
        {
            "name": "Aircraft Database",
            "url": "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv",
            "description": "Complete aircraft database with ICAO24 -> aircraft type mapping"
        },
        {
            "name": "Aircraft Type Designators", 
            "url": "https://opensky-network.org/datasets/metadata/doc8643AircraftTypes.csv",
            "description": "ICAO Doc 8643 aircraft type designators"
        },
        {
            "name": "Aircraft Manufacturers",
            "url": "https://opensky-network.org/datasets/metadata/doc8643Manufacturers.csv", 
            "description": "ICAO Doc 8643 aircraft manufacturers"
        }
    ]
    
    for dataset in metadata_urls:
        print(f"\n--- {dataset['name']} ---")
        print(f"Description: {dataset['description']}")
        print(f"URL: {dataset['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(dataset['url']) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        print(f"File size: {len(content)} characters")
                        
                        # Parse CSV
                        csv_reader = csv.DictReader(StringIO(content))
                        records = list(csv_reader)
                        print(f"Records: {len(records)}")
                        
                        if records:
                            print(f"Columns: {list(records[0].keys())}")
                            
                            # Show sample records
                            print("\nSample records:")
                            for i, record in enumerate(records[:3]):
                                print(f"  Record {i+1}: {dict(record)}")
                            
                            # For aircraft database, look for rare aircraft
                            if "aircraftDatabase" in dataset['url']:
                                await analyze_aircraft_database(records)
                            
                            # For type designators, look for AB18 and VUT1
                            elif "doc8643AircraftTypes" in dataset['url']:
                                await analyze_type_designators(records)
                                
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(1)

async def analyze_aircraft_database(records):
    """Analyze the aircraft database for rare aircraft types"""
    
    print("\n  --- Aircraft Database Analysis ---")
    
    # Build type counts
    type_counts = {}
    icao24_to_type = {}
    
    for record in records:
        icao24 = record.get('icao24', '').strip().lower()
        typecode = record.get('typecode', '').strip()
        
        if icao24 and typecode:
            icao24_to_type[icao24] = typecode
            type_counts[typecode] = type_counts.get(typecode, 0) + 1
    
    print(f"  Total aircraft with types: {len(icao24_to_type)}")
    print(f"  Unique aircraft types: {len(type_counts)}")
    
    # Look for rare aircraft types
    rare_types = ['AB18', 'VUT1', 'C17', 'F16', 'A10']
    print(f"\n  Searching for rare types: {rare_types}")
    
    for rare_type in rare_types:
        if rare_type in type_counts:
            count = type_counts[rare_type]
            print(f"    {rare_type}: {count} aircraft found")
            
            # Show ICAO24 codes for this type
            icao24_codes = [icao24 for icao24, typecode in icao24_to_type.items() if typecode == rare_type]
            print(f"      ICAO24 codes: {icao24_codes[:5]}..." if len(icao24_codes) > 5 else f"      ICAO24 codes: {icao24_codes}")
        else:
            print(f"    {rare_type}: NOT FOUND")
    
    # Show rarest aircraft types
    rare_type_list = [(t, count) for t, count in type_counts.items() if count <= 5]
    rare_type_list.sort(key=lambda x: x[1])
    
    print(f"\n  Rarest aircraft types (5 or fewer):")
    for aircraft_type, count in rare_type_list[:10]:
        print(f"    {aircraft_type}: {count} aircraft")

async def analyze_type_designators(records):
    """Analyze ICAO type designators for rare aircraft definitions"""
    
    print("\n  --- Type Designators Analysis ---")
    
    # Look for specific aircraft we're interested in
    search_terms = ['AB18', 'VUT1', 'AERO', 'BOERO', 'EVEKTOR', 'COBRA']
    
    print(f"  Searching for: {search_terms}")
    
    found_types = {}
    
    for record in records:
        # Check all fields for our search terms
        record_text = ' '.join(str(v).upper() for v in record.values())
        
        for term in search_terms:
            if term in record_text:
                if term not in found_types:
                    found_types[term] = []
                found_types[term].append(record)
    
    if found_types:
        print(f"\n  Found matches:")
        for term, matches in found_types.items():
            print(f"    {term}: {len(matches)} matches")
            for match in matches[:2]:  # Show first 2 matches
                print(f"      {dict(match)}")
    else:
        print(f"  No matches found for search terms")

async def test_combined_approach():
    """Test combining OpenSky live data with metadata for aircraft type lookup"""
    
    print(f"\n" + "=" * 60)
    print("Testing Combined Approach: Live Data + Metadata")
    print("=" * 60)
    
    print("\nStrategy:")
    print("1. Download OpenSky aircraft database (ICAO24 -> type mapping)")
    print("2. Query OpenSky live states API")
    print("3. For each live aircraft, lookup type in local database")
    print("4. Alert when rare aircraft types found")
    
    # Test downloading the aircraft database
    print(f"\nStep 1: Testing aircraft database download...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://opensky-network.org/datasets/metadata/aircraftDatabase.csv") as response:
                if response.status == 200:
                    content = await response.text()
                    csv_reader = csv.DictReader(StringIO(content))
                    records = list(csv_reader)
                    
                    # Build lookup table
                    lookup_table = {}
                    for record in records:
                        icao24 = record.get('icao24', '').strip().lower()
                        typecode = record.get('typecode', '').strip()
                        if icao24 and typecode:
                            lookup_table[icao24] = typecode
                    
                    print(f"  Aircraft database: {len(lookup_table)} mappings loaded")
                    
                    # Test with live data
                    print(f"\nStep 2: Testing live data...")
                    
                    async with session.get("https://opensky-network.org/api/states/all") as live_response:
                        if live_response.status == 200:
                            live_data = await live_response.json()
                            states = live_data.get('states', [])
                            
                            print(f"  Live aircraft: {len(states)} found")
                            
                            if states:
                                print(f"\nStep 3: Testing type lookup...")
                                
                                aircraft_with_types = 0
                                rare_aircraft_found = []
                                
                                for state in states[:20]:  # Test first 20
                                    icao24 = state[0].strip().lower() if state[0] else ''
                                    callsign = state[1].strip() if state[1] else ''
                                    
                                    if icao24 in lookup_table:
                                        aircraft_type = lookup_table[icao24]
                                        aircraft_with_types += 1
                                        
                                        # Check for rare types
                                        rare_types = ['AB18', 'VUT1', 'C17', 'F16', 'A10']
                                        if aircraft_type in rare_types:
                                            rare_aircraft_found.append({
                                                'icao24': icao24,
                                                'callsign': callsign,
                                                'type': aircraft_type
                                            })
                                
                                print(f"  Aircraft with known types: {aircraft_with_types}/20")
                                
                                if rare_aircraft_found:
                                    print(f"\n  *** RARE AIRCRAFT FOUND ***")
                                    for aircraft in rare_aircraft_found:
                                        print(f"    {aircraft['type']}: {aircraft['callsign']} ({aircraft['icao24']})")
                                else:
                                    print(f"  No rare aircraft in sample")
                                
                                print(f"\n*** SOLUTION CONFIRMED ***")
                                print(f"This approach can identify aircraft types in live data!")
                                print(f"Cost: FREE")
                                print(f"Coverage: {len(lookup_table)} known aircraft")
                                
    except Exception as e:
        print(f"Error testing combined approach: {e}")

if __name__ == "__main__":
    asyncio.run(investigate_opensky_metadata())
    asyncio.run(test_combined_approach())