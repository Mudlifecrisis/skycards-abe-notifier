#!/usr/bin/env python3
"""
Quick test of rare aircraft monitoring system
"""
import asyncio
import aiohttp
import json
from datetime import datetime

# Your specific rare aircraft ICAO24 codes (from the database load)
RARE_AIRCRAFT = {
    # Aero Boero AB-180 (AB18)
    'e0d18e': {'type': 'AB18', 'name': 'Aero Boero AB-180'},
    'e0c289': {'type': 'AB18', 'name': 'Aero Boero AB-180'},
    'e0150e': {'type': 'AB18', 'name': 'Aero Boero AB-180'},
    'e013d9': {'type': 'AB18', 'name': 'Aero Boero AB-180'},
    'e01510': {'type': 'AB18', 'name': 'Aero Boero AB-180'},
    
    # Evektor Cobra (VUT1)
    '49c826': {'type': 'VUT1', 'name': 'Evektor Cobra'},
    '4996c5': {'type': 'VUT1', 'name': 'Evektor Cobra'},
    '49d059': {'type': 'VUT1', 'name': 'Evektor Cobra'},
    
    # Some C-17s for testing (more likely to be flying)
    'ae117c': {'type': 'C17', 'name': 'Boeing C-17 Globemaster'},
    'ae1462': {'type': 'C17', 'name': 'Boeing C-17 Globemaster'},
    'ae119c': {'type': 'C17', 'name': 'Boeing C-17 Globemaster'},
}

async def quick_monitor():
    """Quick test of live aircraft monitoring"""
    
    print("Quick Rare Aircraft Monitor Test")
    print("=" * 50)
    print("Watching for specific rare aircraft...")
    print(f"Monitoring {len(RARE_AIRCRAFT)} known rare aircraft")
    print()
    
    for i in range(5):  # Check 5 times
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://opensky-network.org/api/states/all") as response:
                    if response.status == 200:
                        data = await response.json()
                        states = data.get('states', [])
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Checking {len(states)} live aircraft...")
                        
                        found_rare = []
                        
                        for state in states:
                            if not state or len(state) < 1:
                                continue
                                
                            icao24 = state[0].strip().lower() if state[0] else ''
                            
                            if icao24 in RARE_AIRCRAFT:
                                # RARE AIRCRAFT FOUND!
                                callsign = state[1].strip() if state[1] else 'Unknown'
                                lat = state[6] if state[6] else 'Unknown'
                                lon = state[5] if state[5] else 'Unknown'
                                altitude = state[7] if state[7] else 'Unknown'
                                
                                aircraft_info = RARE_AIRCRAFT[icao24]
                                
                                found_rare.append({
                                    'icao24': icao24,
                                    'callsign': callsign,
                                    'type': aircraft_info['type'],
                                    'name': aircraft_info['name'],
                                    'lat': lat,
                                    'lon': lon,
                                    'altitude': altitude
                                })
                        
                        if found_rare:
                            print(f"\n🚨 RARE AIRCRAFT DETECTED! 🚨")
                            for aircraft in found_rare:
                                print(f"  {aircraft['type']}: {aircraft['name']}")
                                print(f"    ICAO24: {aircraft['icao24']}")
                                print(f"    Callsign: {aircraft['callsign']}")
                                print(f"    Position: {aircraft['lat']}, {aircraft['lon']}")
                                print(f"    Altitude: {aircraft['altitude']}")
                                print(f"    Time: {timestamp}")
                                
                                if aircraft['type'] in ['AB18', 'VUT1']:
                                    print(f"    *** THIS IS ONE OF YOUR TARGET RARE AIRCRAFT! ***")
                                print()
                        else:
                            print(f"  No rare aircraft currently detected")
                    
                    else:
                        print(f"API Error: {response.status}")
                        
        except Exception as e:
            print(f"Error: {e}")
        
        if i < 4:  # Don't wait after last iteration
            print("Waiting 15 seconds for next check...")
            await asyncio.sleep(15)
    
    print("\nTest complete!")
    print(f"System ready - if any of your rare aircraft (AB18 or VUT1) appear,")
    print(f"they will be detected and you'll be alerted immediately!")

if __name__ == "__main__":
    asyncio.run(quick_monitor())