#!/usr/bin/env python3
"""
Test live aviation feeds to find which ones include aircraft type in real-time data
"""
import asyncio
import aiohttp
import json

async def test_flightaware_api():
    """Test FlightAware AeroAPI for aircraft type in live data"""
    
    print("Testing FlightAware AeroAPI")
    print("=" * 40)
    
    # FlightAware AeroAPI endpoints
    endpoints = [
        {
            "name": "Flights in Bounds (sample area)",
            "url": "https://aeroapi.flightaware.com/aeroapi/flights/search",
            "description": "Search flights in geographic area"
        },
        {
            "name": "Airport Flights",
            "url": "https://aeroapi.flightaware.com/aeroapi/airports/KABE/flights",
            "description": "Live flights at ABE airport"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n--- {endpoint['name']} ---")
        print(f"URL: {endpoint['url']}")
        
        try:
            # Test without API key first to see response
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint['url']) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response type: {type(data)}")
                        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                    elif response.status == 401:
                        print("Authentication required")
                        # Check response for pricing/plan info
                        response_text = await response.text()
                        if "api" in response_text.lower():
                            print("API key required - checking FlightAware pricing...")
                        
                    else:
                        response_text = await response.text()
                        print(f"Response: {response_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def test_flightradar24_api():
    """Test FlightRadar24 API for aircraft type in live data"""
    
    print("\n" + "=" * 50)
    print("Testing FlightRadar24 API")
    print("=" * 40)
    
    # FlightRadar24 API endpoints (some may be unofficial/deprecated)
    endpoints = [
        {
            "name": "Live Flight Data",
            "url": "https://data-live.flightradar24.com/zones/fcgi/feed.js",
            "description": "Main live flight feed"
        },
        {
            "name": "Aircraft Details",
            "url": "https://data-live.flightradar24.com/clickhandler/?version=1.5&flight=ae117c",
            "description": "Individual aircraft details"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n--- {endpoint['name']} ---")
        print(f"URL: {endpoint['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint['url']) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        # Try to parse as JSON
                        try:
                            data = await response.json()
                            print(f"JSON Response - Type: {type(data)}")
                            
                            if isinstance(data, dict):
                                print(f"Keys: {list(data.keys())}")
                                
                                # Look for aircraft data structure
                                for key, value in data.items():
                                    if isinstance(value, list) and value:
                                        print(f"Array '{key}' has {len(value)} items")
                                        if len(value) > 0:
                                            sample = value[0]
                                            if isinstance(sample, list):
                                                print(f"  Sample item: {sample}")
                                            elif isinstance(sample, dict):
                                                print(f"  Sample keys: {list(sample.keys())}")
                                        break
                            
                        except json.JSONDecodeError:
                            # Not JSON, try as text
                            text = await response.text()
                            print(f"Text response length: {len(text)} chars")
                            
                            # Look for JSONP callback
                            if text.startswith('(') or 'callback' in text:
                                print("Appears to be JSONP format")
                            
                            # Show sample
                            print(f"Sample: {text[:300]}...")
                            
                    else:
                        response_text = await response.text()
                        print(f"Error response: {response_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def test_adsbx_live_type_data():
    """Re-test ADS-B Exchange specifically for aircraft type in live feeds"""
    
    print("\n" + "=" * 50)
    print("Re-testing ADS-B Exchange for Aircraft Type")
    print("=" * 40)
    
    # Focus on endpoints that might include type data
    endpoints = [
        {
            "name": "Geographic area with military focus",
            "url": "https://adsbexchange.com/api/aircraft/lat/39.0458/lon/-76.6413/dist/50/",
            "description": "Area around Andrews AFB (military aircraft likely)"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n--- {endpoint['name']} ---")
        print(f"URL: {endpoint['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint['url']) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Look for aircraft array
                        aircraft_list = data.get('aircraft', data.get('ac', []))
                        print(f"Aircraft found: {len(aircraft_list)}")
                        
                        if aircraft_list:
                            print("\nAnalyzing aircraft data structure...")
                            sample = aircraft_list[0]
                            print(f"Sample aircraft fields: {list(sample.keys())}")
                            
                            # Specifically look for type-related fields
                            type_fields = ['t', 'type', 'typecode', 'aircraft_type', 'actype', 'model', 'manufacturer']
                            found_type_fields = [f for f in type_fields if f in sample]
                            
                            if found_type_fields:
                                print(f"Type fields found: {found_type_fields}")
                                for field in found_type_fields:
                                    print(f"  {field}: {sample.get(field)}")
                            else:
                                print("NO TYPE FIELDS FOUND in live data")
                            
                    else:
                        print(f"Error: {response.status}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def research_api_pricing():
    """Research API pricing for services that might include aircraft type"""
    
    print("\n" + "=" * 50)
    print("API Pricing Research")
    print("=" * 40)
    
    pricing_info = {
        "FlightAware AeroAPI": {
            "free_tier": "Unknown",
            "paid_plans": "Check website",
            "aircraft_type": "Likely includes aircraft type",
            "url": "https://www.flightaware.com/commercial/aeroapi/"
        },
        "AviationStack": {
            "free_tier": "1000 requests/month",
            "paid_plans": "$9.99/month for 10K requests",
            "aircraft_type": "Unknown - needs testing",
            "url": "https://aviationstack.com/pricing"
        },
        "AirLabs": {
            "free_tier": "1000 requests/month", 
            "paid_plans": "$9.99/month for 10K requests",
            "aircraft_type": "Includes aircraft info",
            "url": "https://airlabs.co/pricing"
        }
    }
    
    for service, info in pricing_info.items():
        print(f"\n{service}:")
        for key, value in info.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_flightaware_api())
    asyncio.run(test_flightradar24_api())
    asyncio.run(test_adsbx_live_type_data())
    asyncio.run(research_api_pricing())