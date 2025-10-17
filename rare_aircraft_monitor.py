#!/usr/bin/env python3
"""
Rare Aircraft Monitor using OpenSky live feed + metadata database
Monitors for AB18 (Aero Boero AB-180), VUT1 (Evektor Cobra), and other rare aircraft
"""
import asyncio
import aiohttp
import csv
from io import StringIO
import json
from datetime import datetime
import time

class RareAircraftMonitor:
    def __init__(self):
        self.aircraft_database = {}  # ICAO24 -> aircraft info
        self.rare_types = {
            'AB18': 'Aero Boero AB-180',
            'VUT1': 'Evektor Cobra',
            'C17': 'Boeing C-17 Globemaster',
            'F16': 'F-16 Fighting Falcon',
            'A10': 'A-10 Thunderbolt II'
        }
        self.known_rare_icao24s = set()  # Track which rare aircraft we know about
        self.detected_aircraft = set()  # Track aircraft we've already alerted on
        
    async def load_aircraft_database(self):
        """Download and load OpenSky aircraft database"""
        
        print("Loading OpenSky Aircraft Database...")
        print("=" * 50)
        
        db_url = "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv"
        
        try:
            async with aiohttp.ClientSession() as session:
                print("Downloading aircraft database (this may take a moment)...")
                async with session.get(db_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"Downloaded {len(content)} characters")
                        
                        # Parse CSV
                        csv_reader = csv.DictReader(StringIO(content))
                        
                        total_aircraft = 0
                        rare_aircraft_found = 0
                        
                        for record in csv_reader:
                            icao24 = record.get('icao24', '').strip().lower()
                            typecode = record.get('typecode', '').strip()
                            
                            if icao24 and typecode:
                                # Store aircraft info
                                self.aircraft_database[icao24] = {
                                    'type': typecode,
                                    'registration': record.get('registration', ''),
                                    'model': record.get('model', ''),
                                    'manufacturer': record.get('manufacturername', ''),
                                    'operator': record.get('operator', '')
                                }
                                total_aircraft += 1
                                
                                # Track rare aircraft
                                if typecode in self.rare_types:
                                    self.known_rare_icao24s.add(icao24)
                                    rare_aircraft_found += 1
                                    print(f"  Found rare aircraft: {icao24} -> {typecode} ({self.rare_types[typecode]})")
                        
                        print(f"\nDatabase loaded successfully!")
                        print(f"Total aircraft: {total_aircraft:,}")
                        print(f"Rare aircraft types found: {rare_aircraft_found}")
                        
                        # Show breakdown by rare type
                        for rare_type, description in self.rare_types.items():
                            count = sum(1 for info in self.aircraft_database.values() if info['type'] == rare_type)
                            print(f"  {rare_type} ({description}): {count} aircraft")
                        
                        return True
                        
                    else:
                        print(f"Failed to download database: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            print(f"Error loading aircraft database: {e}")
            return False
    
    async def monitor_live_aircraft(self):
        """Monitor OpenSky live feed for rare aircraft"""
        
        print(f"\nStarting Live Aircraft Monitoring...")
        print("=" * 50)
        print("Monitoring for rare aircraft types:")
        for rare_type, description in self.rare_types.items():
            print(f"  {rare_type}: {description}")
        print(f"Press Ctrl+C to stop monitoring\n")
        
        consecutive_errors = 0
        max_errors = 5
        
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://opensky-network.org/api/states/all") as response:
                        if response.status == 200:
                            consecutive_errors = 0  # Reset error counter
                            
                            data = await response.json()
                            states = data.get('states', [])
                            
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] Checking {len(states)} live aircraft...")
                            
                            rare_found = 0
                            
                            for state in states:
                                if not state or len(state) < 1:
                                    continue
                                    
                                icao24 = state[0].strip().lower() if state[0] else ''
                                callsign = state[1].strip() if state[1] else 'Unknown'
                                
                                # Check if this is a rare aircraft
                                if icao24 in self.aircraft_database:
                                    aircraft_info = self.aircraft_database[icao24]
                                    aircraft_type = aircraft_info['type']
                                    
                                    if aircraft_type in self.rare_types:
                                        # Found rare aircraft!
                                        alert_key = f"{icao24}_{callsign}"
                                        
                                        if alert_key not in self.detected_aircraft:
                                            # New rare aircraft detection
                                            self.detected_aircraft.add(alert_key)
                                            
                                            lat = state[6] if state[6] else 'Unknown'
                                            lon = state[5] if state[5] else 'Unknown'
                                            altitude = state[7] if state[7] else 'Unknown'
                                            
                                            print(f"\n🚨 RARE AIRCRAFT DETECTED! 🚨")
                                            print(f"Type: {aircraft_type} ({self.rare_types[aircraft_type]})")
                                            print(f"ICAO24: {icao24}")
                                            print(f"Callsign: {callsign}")
                                            print(f"Registration: {aircraft_info['registration']}")
                                            print(f"Model: {aircraft_info['model']}")
                                            print(f"Operator: {aircraft_info['operator']}")
                                            print(f"Position: {lat}, {lon}")
                                            print(f"Altitude: {altitude}")
                                            print(f"Time: {timestamp}")
                                            print("=" * 60)
                                            
                                        rare_found += 1
                            
                            if rare_found > 0:
                                print(f"Active rare aircraft: {rare_found}")
                            
                        else:
                            consecutive_errors += 1
                            print(f"API error: HTTP {response.status} (error {consecutive_errors}/{max_errors})")
                            
                            if consecutive_errors >= max_errors:
                                print(f"Too many consecutive errors. Stopping monitor.")
                                break
                
                # Wait before next check (OpenSky recommends 10-second intervals)
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\nMonitoring stopped by user")
                break
                
            except Exception as e:
                consecutive_errors += 1
                print(f"Error during monitoring: {e} (error {consecutive_errors}/{max_errors})")
                
                if consecutive_errors >= max_errors:
                    print(f"Too many consecutive errors. Stopping monitor.")
                    break
                
                await asyncio.sleep(10)
    
    async def search_specific_aircraft(self, search_term):
        """Search for specific aircraft in the database"""
        
        print(f"Searching for: {search_term}")
        print("=" * 40)
        
        search_term = search_term.upper()
        matches = []
        
        for icao24, info in self.aircraft_database.items():
            if (search_term in info['type'].upper() or 
                search_term in info['model'].upper() or
                search_term in info['registration'].upper()):
                matches.append((icao24, info))
        
        if matches:
            print(f"Found {len(matches)} matches:")
            for icao24, info in matches[:10]:  # Show first 10
                print(f"  {icao24}: {info['type']} - {info['model']} ({info['registration']})")
        else:
            print("No matches found")
        
        return matches

async def main():
    """Main function to run the rare aircraft monitor"""
    
    print("Rare Aircraft Monitor")
    print("=" * 60)
    print("Monitoring for:")
    print("  AB18: Aero Boero AB-180")
    print("  VUT1: Evektor Cobra")
    print("  C17: Boeing C-17 Globemaster")
    print("  F16: F-16 Fighting Falcon")
    print("  A10: A-10 Thunderbolt II")
    print("=" * 60)
    
    monitor = RareAircraftMonitor()
    
    # Load aircraft database
    if await monitor.load_aircraft_database():
        print(f"\nReady to monitor! Known rare aircraft ICAO24 codes:")
        for icao24 in sorted(monitor.known_rare_icao24s):
            if icao24 in monitor.aircraft_database:
                info = monitor.aircraft_database[icao24]
                print(f"  {icao24}: {info['type']} - {info['registration']}")
        
        # Start monitoring
        await monitor.monitor_live_aircraft()
    else:
        print("Failed to load aircraft database. Cannot start monitoring.")

if __name__ == "__main__":
    asyncio.run(main())