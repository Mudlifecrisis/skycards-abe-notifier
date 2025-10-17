#!/usr/bin/env python3
"""
Test free aviation APIs that might include aircraft type information
"""
import asyncio
import aiohttp
import json

async def test_free_aviation_apis():
    """Test free aviation APIs for aircraft type inclusion"""
    
    print("Testing Free Aviation APIs for Aircraft Type")
    print("=" * 60)
    
    # Free APIs to test
    apis = [
        {
            "name": "OpenSky Network States",
            "url": "https://opensky-network.org/api/states/all",
            "description": "OpenSky live aircraft states (no auth required)"
        },
        {
            "name": "AviationStack Free Trial",
            "url": "https://api.aviationstack.com/v1/flights?access_key=YOUR_FREE_KEY",
            "description": "AviationStack (requires free signup)"
        },
        {
            "name": "AirLabs Free Trial", 
            "url": "https://airlabs.co/api/v9/flights?api_key=YOUR_FREE_KEY",
            "description": "AirLabs (requires free signup)"
        },
        {
            "name": "FlightRadar24 Alternative",
            "url": "https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds=90,-180,-90,180",
            "description": "FlightRadar24 alternative endpoint"
        }
    ]
    
    for api in apis:
        print(f"\n--- {api['name']} ---")
        print(f"Description: {api['description']}")
        
        # Skip APIs that require keys for now
        if "YOUR_FREE_KEY" in api['url']:
            print("Requires API key - skipping direct test")
            continue
            
        print(f"URL: {api['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api['url'], timeout=30) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        # Try to parse response
                        try:
                            data = await response.json()
                            await analyze_api_response(api['name'], data)
                            
                        except json.JSONDecodeError:
                            text = await response.text()
                            print(f"Non-JSON response length: {len(text)} chars")
                            
                            # Check for JSONP
                            if text.strip().startswith('(') or 'callback' in text[:100]:
                                print("Appears to be JSONP - needs special parsing")
                            else:
                                print(f"Sample text: {text[:200]}...")
                    
                    elif response.status == 401:
                        print("Authentication required")
                    elif response.status == 403:
                        print("Access forbidden")
                    else:
                        response_text = await response.text()
                        print(f"Error response: {response_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(1)  # Rate limiting

async def analyze_api_response(api_name, data):
    """Analyze API response for aircraft type information"""
    
    print(f"Analyzing {api_name} response...")
    
    if isinstance(data, dict):
        print(f"Response type: dict with keys: {list(data.keys())}")
        
        # Look for aircraft data arrays
        aircraft_arrays = []
        for key, value in data.items():
            if isinstance(value, list) and value:
                aircraft_arrays.append((key, len(value)))
        
        if aircraft_arrays:
            print(f"Found arrays: {aircraft_arrays}")
            
            # Analyze the largest array (likely aircraft data)
            largest_array_key = max(aircraft_arrays, key=lambda x: x[1])[0]
            aircraft_data = data[largest_array_key]
            
            print(f"Analyzing array '{largest_array_key}' with {len(aircraft_data)} items")
            
            if aircraft_data:
                sample = aircraft_data[0]
                print(f"Sample item type: {type(sample)}")
                
                if isinstance(sample, list):
                    print(f"Array item structure: {len(sample)} elements")
                    print(f"Sample: {sample}")
                    
                    # For OpenSky format, check if aircraft type is included
                    if api_name == "OpenSky Network States" and len(sample) >= 11:
                        print("\nOpenSky States format analysis:")
                        print(f"  ICAO24: {sample[0]}")
                        print(f"  Callsign: {sample[1]}")
                        print(f"  Country: {sample[2]}")
                        print(f"  Position: lat={sample[6]}, lon={sample[5]}")
                        print(f"  All fields: {sample}")
                        print("  *** NO AIRCRAFT TYPE FIELD IN OPENSKY STATES ***")
                
                elif isinstance(sample, dict):
                    print(f"Dict item keys: {list(sample.keys())}")
                    
                    # Look for aircraft type fields
                    type_fields = ['aircraft_type', 'type', 'typecode', 'aircraft', 'model', 'manufacturer']
                    found_type_fields = [f for f in type_fields if f in sample]
                    
                    if found_type_fields:
                        print(f"*** AIRCRAFT TYPE FIELDS FOUND: {found_type_fields} ***")
                        for field in found_type_fields:
                            print(f"  {field}: {sample[field]}")
                    else:
                        print("No aircraft type fields found")
        
        else:
            print("No arrays found in response")
    
    elif isinstance(data, list):
        print(f"Response type: list with {len(data)} items")
        if data:
            sample = data[0]
            print(f"Sample item: {sample}")
    
    else:
        print(f"Response type: {type(data)}")

async def research_api_signup_process():
    """Research the signup process for APIs with free tiers"""
    
    print("\n" + "=" * 60)
    print("Free API Signup Research")
    print("=" * 30)
    
    free_apis = {
        "AviationStack": {
            "free_tier": "1,000 requests/month",
            "signup_url": "https://aviationstack.com/signup/free",
            "includes_aircraft_type": "Yes (aircraft.iata, aircraft.icao)",
            "cost_after_free": "$9.99/month for 10,000 requests"
        },
        "AirLabs": {
            "free_tier": "1,000 requests/month", 
            "signup_url": "https://airlabs.co/signup",
            "includes_aircraft_type": "Yes (aircraft_code field)",
            "cost_after_free": "$9.99/month for 10,000 requests"
        },
        "FlightAware AeroAPI": {
            "free_tier": "Unknown - may have trial",
            "signup_url": "https://www.flightaware.com/commercial/aeroapi/",
            "includes_aircraft_type": "Yes (full aircraft details)",
            "cost_after_free": "Contact for pricing"
        }
    }
    
    print("APIs with free tiers that include aircraft type:")
    for api_name, info in free_apis.items():
        print(f"\n{api_name}:")
        for key, value in info.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_free_aviation_apis())
    asyncio.run(research_api_signup_process())