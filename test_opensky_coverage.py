#!/usr/bin/env python3
"""
Test OpenSky Network coverage for specific aircraft
"""
import asyncio
import aiohttp
import json
import os
from datetime import datetime

async def test_opensky_coverage():
    """Test if we can find RCH4231 on OpenSky"""
    
    # Load OpenSky credentials
    opensky_config = json.loads(os.getenv("OPENSKY_API", "{}"))
    
    print("Testing OpenSky Network coverage...")
    print(f"Looking for: RCH4231 (hex: AE117C)")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test 1: Get all states and look for our aircraft
    try:
        auth = aiohttp.BasicAuth(
            opensky_config.get("clientId", ""),
            opensky_config.get("clientSecret", "")
        )
        
        async with aiohttp.ClientSession(auth=auth) as session:
            # Get all current aircraft states
            url = "https://opensky-network.org/api/states/all"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    states = data.get('states', [])
                    
                    print(f"Total aircraft in OpenSky: {len(states)}")
                    
                    # Look for our specific aircraft
                    found_rch4231 = False
                    rch_aircraft = []
                    
                    for state in states:
                        icao24 = state[0]
                        callsign = (state[1] or "").strip()
                        
                        # Check for our specific aircraft
                        if icao24.upper() == "AE117C" or callsign == "RCH4231":
                            found_rch4231 = True
                            print(f"FOUND RCH4231:")
                            print(f"   ICAO24: {icao24}")
                            print(f"   Callsign: {callsign}")
                            print(f"   Position: {state[6]}, {state[5]}")
                            print(f"   Altitude: {state[7]} meters")
                            print(f"   Velocity: {state[9]} m/s")
                            
                        # Collect all RCH aircraft
                        if callsign.startswith("RCH"):
                            rch_aircraft.append({
                                'icao24': icao24,
                                'callsign': callsign,
                                'lat': state[6],
                                'lon': state[5],
                                'altitude': state[7],
                                'velocity': state[9]
                            })
                    
                    if not found_rch4231:
                        print("RCH4231 not found in OpenSky data")
                        
                    print(f"\nFound {len(rch_aircraft)} RCH aircraft in OpenSky:")
                    for aircraft in rch_aircraft:
                        print(f"  {aircraft['callsign']} ({aircraft['icao24']})")
                        
                else:
                    print(f"OpenSky API error: {resp.status}")
                    
    except Exception as e:
        print(f"Error testing OpenSky: {e}")

    # Test 2: Compare with what our rare hunter would find
    print("\n" + "="*50)
    print("Testing our rare hunter logic...")
    
    try:
        from rare_hunter import RareAircraftHunter
        hunter = RareAircraftHunter()
        
        print("Forcing rare aircraft search...")
        rare_aircraft = await hunter.find_rare_aircraft()
        
        print(f"Our hunter found {len(rare_aircraft)} rare aircraft:")
        for aircraft in rare_aircraft:
            callsign = aircraft.get('callsign', 'Unknown')
            matched_term = aircraft.get('matched_term', '')
            if callsign.startswith('RCH'):
                print(f"  FOUND: {callsign} (matched: {matched_term})")
            else:
                print(f"  {callsign} (matched: {matched_term})")
                
    except Exception as e:
        print(f"Error testing rare hunter: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_opensky_coverage())