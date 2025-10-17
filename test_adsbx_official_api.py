#!/usr/bin/env python3
"""
Test official ADS-B Exchange API endpoints
"""
import asyncio
import aiohttp
import json

async def test_adsbx_official_endpoints():
    """Test official ADS-B Exchange API endpoints"""
    
    print("Testing Official ADS-B Exchange API Endpoints")
    print("=" * 60)
    
    # Test endpoints from the documentation
    endpoints = [
        {
            "name": "Geographic Search (London area)",
            "url": "https://adsbexchange.com/api/aircraft/lat/51.5005/lon/-0.1145/dist/100/",
            "description": "All aircraft within 100NM of London"
        },
        {
            "name": "Geographic Search (ABE area)", 
            "url": "https://adsbexchange.com/api/aircraft/lat/40.6522/lon/-75.4402/dist/100/",
            "description": "All aircraft within 100NM of ABE airport"
        },
        {
            "name": "Known C-17 by ICAO",
            "url": "https://adsbexchange.com/api/aircraft/icao/ae117c/",
            "description": "Specific aircraft lookup (RCH4231)"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n--- {endpoint['name']} ---")
        print(f"URL: {endpoint['url']}")
        print(f"Description: {endpoint['description']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint['url'], timeout=30) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response type: {type(data)}")
                        
                        # Handle different response structures
                        aircraft_list = []
                        if isinstance(data, dict):
                            aircraft_list = data.get('aircraft', data.get('ac', []))
                        elif isinstance(data, list):
                            aircraft_list = data
                        
                        print(f"Aircraft found: {len(aircraft_list)}")
                        
                        if aircraft_list:
                            print("\nSample aircraft (first 3):")
                            for i, aircraft in enumerate(aircraft_list[:3]):
                                print(f"\nAircraft {i+1}:")
                                
                                # Check for aircraft type information
                                type_info = None
                                type_fields = ['t', 'type', 'typecode', 'aircraft_type', 'actype', 'dbFlags']
                                
                                for field in type_fields:
                                    if field in aircraft and aircraft[field]:
                                        type_info = aircraft[field]
                                        print(f"  Type ({field}): {type_info}")
                                        break
                                
                                if not type_info:
                                    print("  Type: NOT FOUND")
                                
                                # Show key identification fields
                                key_fields = ['hex', 'flight', 'r', 'alt_baro', 'gs', 'lat', 'lon']
                                for field in key_fields:
                                    if field in aircraft and aircraft[field] is not None:
                                        print(f"  {field}: {aircraft[field]}")
                                
                                # Show all available fields
                                print(f"  All fields: {sorted(list(aircraft.keys()))}")
                            
                            # Count aircraft with type information
                            typed_aircraft = 0
                            for aircraft in aircraft_list:
                                for field in ['t', 'type', 'typecode', 'aircraft_type', 'actype']:
                                    if field in aircraft and aircraft[field]:
                                        typed_aircraft += 1
                                        break
                            
                            print(f"\nAircraft with type info: {typed_aircraft}/{len(aircraft_list)} ({typed_aircraft/len(aircraft_list)*100:.1f}%)")
                        
                    elif response.status == 403:
                        print("Access forbidden - may require API key")
                    elif response.status == 404:
                        print("Endpoint not found or no data")
                    else:
                        print(f"Error: HTTP {response.status}")
                        response_text = await response.text()
                        print(f"Response: {response_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(1)  # Rate limiting
    
    print("\n" + "=" * 60)
    print("Analysis: Checking if ADS-B Exchange provides aircraft type in live feeds")

if __name__ == "__main__":
    asyncio.run(test_adsbx_official_endpoints())