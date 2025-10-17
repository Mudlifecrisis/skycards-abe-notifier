#!/usr/bin/env python3
"""
Test ADS-B Exchange API to see if they provide aircraft type in live feeds
"""
import asyncio
import aiohttp
import json

async def test_adsbexchange_api():
    """Test ADS-B Exchange API for aircraft type data"""
    
    print("Testing ADS-B Exchange API")
    print("=" * 50)
    
    # ADS-B Exchange endpoints to test
    endpoints = [
        {
            "name": "Global Aircraft Feed",
            "url": "https://globe.adsbexchange.com/data/aircraft.json",
            "description": "Main global aircraft feed"
        },
        {
            "name": "US Military Feed", 
            "url": "https://globe.adsbexchange.com/data/mil.json",
            "description": "Military aircraft specific feed"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n--- Testing {endpoint['name']} ---")
        print(f"URL: {endpoint['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint['url'], timeout=30) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Analyze data structure
                        aircraft_list = data.get('aircraft', [])
                        if not aircraft_list:
                            aircraft_list = data.get('ac', [])  # Alternative key
                        
                        print(f"Aircraft count: {len(aircraft_list)}")
                        
                        if aircraft_list:
                            # Examine first few aircraft for data structure
                            print("\nSample aircraft data:")
                            for i, aircraft in enumerate(aircraft_list[:3]):
                                print(f"\nAircraft {i+1}:")
                                
                                # Look for aircraft type fields
                                type_fields = ['t', 'type', 'typecode', 'aircraft_type', 'actype', 'model']
                                found_type = False
                                
                                for field in type_fields:
                                    if field in aircraft and aircraft[field]:
                                        print(f"  Aircraft Type ({field}): {aircraft[field]}")
                                        found_type = True
                                
                                if not found_type:
                                    print("  Aircraft Type: NOT FOUND")
                                
                                # Show other relevant fields
                                relevant_fields = ['hex', 'flight', 'r', 'alt_baro', 'gs']
                                for field in relevant_fields:
                                    if field in aircraft:
                                        print(f"  {field}: {aircraft[field]}")
                                
                                # Show all available fields for analysis
                                print(f"  Available fields: {list(aircraft.keys())}")
                        
                        # Look for aircraft with type information
                        aircraft_with_types = []
                        for aircraft in aircraft_list[:20]:  # Check first 20
                            for type_field in ['t', 'type', 'typecode', 'aircraft_type', 'actype']:
                                if type_field in aircraft and aircraft[type_field]:
                                    aircraft_with_types.append({
                                        'hex': aircraft.get('hex', 'unknown'),
                                        'flight': aircraft.get('flight', '').strip(),
                                        'type': aircraft[type_field]
                                    })
                                    break
                        
                        print(f"\nAircraft with type information: {len(aircraft_with_types)}")
                        if aircraft_with_types:
                            print("Examples:")
                            for example in aircraft_with_types[:5]:
                                print(f"  {example['flight']:10} ({example['hex']}) → {example['type']}")
                        
                    else:
                        print(f"Error: HTTP {response.status}")
                        
        except Exception as e:
            print(f"Error testing {endpoint['name']}: {e}")
    
    print("\n" + "=" * 50)
    print("ADS-B Exchange Analysis Complete")

if __name__ == "__main__":
    asyncio.run(test_adsbexchange_api())