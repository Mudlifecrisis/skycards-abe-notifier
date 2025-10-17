#!/usr/bin/env python3
"""
Detailed analysis of FlightRadar24 API to check for aircraft type data
"""
import asyncio
import aiohttp
import json

async def analyze_flightradar24_data():
    """Analyze FlightRadar24 live feed structure for aircraft type"""
    
    print("Detailed FlightRadar24 Data Analysis")
    print("=" * 50)
    
    # Main live feed
    feed_url = "https://data-live.flightradar24.com/zones/fcgi/feed.js"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url) as response:
                print(f"Feed Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    aircraft_data = data.get('aircraft', {})
                    print(f"Aircraft entries: {len(aircraft_data)}")
                    
                    if aircraft_data:
                        # Analyze aircraft data structure
                        print(f"\nAnalyzing aircraft data structure...")
                        
                        # Get first few aircraft for analysis
                        aircraft_keys = list(aircraft_data.keys())[:5]
                        
                        for i, aircraft_id in enumerate(aircraft_keys):
                            aircraft_info = aircraft_data[aircraft_id]
                            print(f"\nAircraft {i+1} (ID: {aircraft_id}):")
                            print(f"  Data type: {type(aircraft_info)}")
                            
                            if isinstance(aircraft_info, list):
                                print(f"  Array length: {len(aircraft_info)}")
                                print(f"  Array content: {aircraft_info}")
                                
                                # FlightRadar24 typically uses arrays with positional data
                                # Common format: [hex, lat, lon, track, alt, speed, squawk, radar, aircraft_type, reg, timestamp, from, to, flight, ...]
                                if len(aircraft_info) > 8:
                                    print(f"\n  Parsing FlightRadar24 format:")
                                    print(f"    Index 0 (hex): {aircraft_info[0] if len(aircraft_info) > 0 else 'N/A'}")
                                    print(f"    Index 1 (lat): {aircraft_info[1] if len(aircraft_info) > 1 else 'N/A'}")
                                    print(f"    Index 2 (lon): {aircraft_info[2] if len(aircraft_info) > 2 else 'N/A'}")
                                    print(f"    Index 8 (aircraft_type): {aircraft_info[8] if len(aircraft_info) > 8 else 'N/A'}")
                                    print(f"    Index 9 (registration): {aircraft_info[9] if len(aircraft_info) > 9 else 'N/A'}")
                                    print(f"    Index 13 (flight): {aircraft_info[13] if len(aircraft_info) > 13 else 'N/A'}")
                                    
                                    # Check if index 8 contains aircraft type
                                    if len(aircraft_info) > 8 and aircraft_info[8]:
                                        aircraft_type = aircraft_info[8]
                                        print(f"    *** AIRCRAFT TYPE FOUND: {aircraft_type} ***")
                                        
                            elif isinstance(aircraft_info, dict):
                                print(f"  Dict keys: {list(aircraft_info.keys())}")
                        
                        # Count aircraft with type information
                        aircraft_with_types = 0
                        type_examples = {}
                        
                        for aircraft_id, aircraft_info in aircraft_data.items():
                            if isinstance(aircraft_info, list) and len(aircraft_info) > 8:
                                aircraft_type = aircraft_info[8]
                                if aircraft_type and aircraft_type.strip():
                                    aircraft_with_types += 1
                                    
                                    # Collect type examples
                                    if aircraft_type not in type_examples:
                                        type_examples[aircraft_type] = []
                                    if len(type_examples[aircraft_type]) < 3:
                                        flight = aircraft_info[13] if len(aircraft_info) > 13 else 'Unknown'
                                        type_examples[aircraft_type].append(flight)
                        
                        print(f"\n--- AIRCRAFT TYPE ANALYSIS ---")
                        print(f"Total aircraft: {len(aircraft_data)}")
                        print(f"Aircraft with type info: {aircraft_with_types}")
                        print(f"Percentage with types: {aircraft_with_types/len(aircraft_data)*100:.1f}%")
                        
                        print(f"\nAircraft types found: {len(type_examples)}")
                        for aircraft_type, flights in list(type_examples.items())[:10]:
                            print(f"  {aircraft_type}: {flights}")
                        
                        # Look specifically for rare aircraft types
                        rare_types = ['AB18', 'VUT1', 'C17']
                        print(f"\nSearching for rare types: {rare_types}")
                        
                        for aircraft_id, aircraft_info in aircraft_data.items():
                            if isinstance(aircraft_info, list) and len(aircraft_info) > 8:
                                aircraft_type = aircraft_info[8]
                                if aircraft_type in rare_types:
                                    flight = aircraft_info[13] if len(aircraft_info) > 13 else 'Unknown'
                                    hex_code = aircraft_info[0] if len(aircraft_info) > 0 else 'Unknown'
                                    print(f"  RARE AIRCRAFT FOUND: {aircraft_type} - Flight: {flight} - Hex: {hex_code}")
                    
    except Exception as e:
        print(f"Error analyzing FlightRadar24: {e}")

async def test_aviationstack_api():
    """Test AviationStack API for aircraft type"""
    
    print("\n" + "=" * 50)
    print("Testing AviationStack API")
    print("=" * 30)
    
    # AviationStack endpoints
    endpoints = [
        "http://api.aviationstack.com/v1/flights",
        "http://api.aviationstack.com/v1/flights?flight_status=active"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting: {endpoint}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                    elif response.status == 401:
                        print("API key required")
                        
                    else:
                        response_text = await response.text()
                        print(f"Response: {response_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def test_airlabs_api():
    """Test AirLabs API for aircraft type"""
    
    print("\n" + "=" * 50)
    print("Testing AirLabs API")
    print("=" * 30)
    
    # AirLabs endpoints
    endpoints = [
        "https://airlabs.co/api/v9/flights",
        "https://airlabs.co/api/v9/schedules"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting: {endpoint}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                    elif response.status == 401:
                        print("API key required")
                        
                    else:
                        response_text = await response.text()
                        print(f"Response: {response_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_flightradar24_data())
    asyncio.run(test_aviationstack_api())
    asyncio.run(test_airlabs_api())