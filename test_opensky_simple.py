#!/usr/bin/env python3
"""
Test OpenSky Network without authentication
"""
import asyncio
import aiohttp
from datetime import datetime

async def test_opensky_anonymous():
    """Test OpenSky without authentication"""
    
    print("Testing OpenSky Network (anonymous)...")
    print(f"Looking for: RCH4231 (hex: AE117C)")
    print(f"Time: {datetime.now()}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get all current aircraft states (no auth)
            url = "https://opensky-network.org/api/states/all"
            print(f"Requesting: {url}")
            
            async with session.get(url) as resp:
                print(f"Response status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    states = data.get('states', [])
                    
                    print(f"Total aircraft in OpenSky: {len(states)}")
                    
                    # Look for our specific aircraft and all RCH aircraft
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
                        alt_ft = aircraft['altitude'] * 3.28084 if aircraft['altitude'] else 0
                        vel_kts = aircraft['velocity'] * 1.94384 if aircraft['velocity'] else 0
                        print(f"  {aircraft['callsign']} ({aircraft['icao24']}) - {alt_ft:.0f}ft, {vel_kts:.0f}kts")
                        
                    # Show some sample aircraft to verify data is coming through
                    print(f"\nSample of first 5 aircraft:")
                    for i, state in enumerate(states[:5]):
                        icao24 = state[0]
                        callsign = (state[1] or "").strip()
                        print(f"  {callsign or 'N/A'} ({icao24})")
                        
                elif resp.status == 429:
                    print("Rate limited - too many requests")
                else:
                    print(f"API error: {resp.status}")
                    text = await resp.text()
                    print(f"Response: {text[:200]}")
                    
    except Exception as e:
        print(f"Error testing OpenSky: {e}")

if __name__ == "__main__":
    asyncio.run(test_opensky_anonymous())