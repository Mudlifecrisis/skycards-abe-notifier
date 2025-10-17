#!/usr/bin/env python3
"""
Test OpenSky's free aircraft database
"""
import asyncio
import aiohttp
import json

async def test_opensky_aircraft_database():
    """Test OpenSky's aircraft database with known C-17s"""
    
    # Known C-17 ICAO24 codes from our previous detection
    test_icao24s = [
        "ae117c",  # RCH4231 - the missing aircraft
        "ae1462",  # RCH3241 - detected before
        "ae119c",  # RCH808 - detected before
        "ae07d4",  # RCH183 - detected before
    ]
    
    print("Testing OpenSky Aircraft Database (FREE)")
    print("=" * 50)
    
    for icao24 in test_icao24s:
        print(f"\nTesting ICAO24: {icao24}")
        
        try:
            url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"  SUCCESS: {json.dumps(data, indent=2)}")
                        
                        # Check if we get aircraft type
                        aircraft_type = data.get('typecode') or data.get('aircraftTypeDesignator')
                        if aircraft_type:
                            print(f"  SUCCESS Aircraft Type: {aircraft_type}")
                        else:
                            print(f"  MISSING No aircraft type found")
                            
                    elif response.status == 404:
                        print(f"  NOT FOUND Aircraft not found in OpenSky database")
                    else:
                        print(f"  ERROR: {response.status}")
                        
        except Exception as e:
            print(f"  EXCEPTION: {e}")
    
    print("\n" + "=" * 50)
    print("Summary: Testing if OpenSky has aircraft type data for known C-17s")

if __name__ == "__main__":
    asyncio.run(test_opensky_aircraft_database())