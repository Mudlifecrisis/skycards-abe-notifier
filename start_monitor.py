#!/usr/bin/env python3
"""
Start the rare aircraft monitor without Unicode issues
"""
import asyncio
import aiohttp
import json
import os
import time
import winsound
from datetime import datetime
import logging

class RareAircraftMonitor:
    def __init__(self):
        self.config = None
        self.aircraft_db = {}
        self.user_targets = {}
        self.rare_aircraft = {}
        self.detected_aircraft = set()
        self.consecutive_errors = 0
        self.total_checks = 0
        self.total_detections = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('aircraft_data/monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config_and_database(self):
        """Load configuration and aircraft database"""
        
        # Load config
        try:
            with open("aircraft_data/monitoring_config.json", 'r') as f:
                self.config = json.load(f)
            print("Configuration loaded successfully")
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
            
        # Load database
        try:
            print("Loading aircraft database...")
            with open("aircraft_data/production_aircraft_database.json", 'r') as f:
                db_data = json.load(f)
            
            self.aircraft_db = db_data['aircraft']
            self.user_targets = db_data['user_targets']
            self.rare_aircraft = db_data['rare_aircraft']
            
            print(f"Database loaded:")
            print(f"  Total aircraft: {len(self.aircraft_db):,}")
            print(f"  Your target aircraft: {len(self.user_targets)}")
            print(f"  All rare aircraft: {len(self.rare_aircraft)}")
            
            return True
            
        except Exception as e:
            print(f"Error loading database: {e}")
            return False
    
    def alert_detection(self, icao24, aircraft_info, callsign, position, altitude):
        """Handle aircraft detection alert"""
        
        aircraft_type = aircraft_info['type']
        
        # Determine if this is your target aircraft
        if aircraft_type in ['AB18', 'VUT1']:
            priority = "HIGH"
            type_names = {'AB18': 'Aero Boero AB-180', 'VUT1': 'Evektor Cobra'}
            type_name = type_names[aircraft_type]
            
            print(f"\n" + "="*60)
            print(f"*** YOUR TARGET RARE AIRCRAFT DETECTED! ***")
            print(f"="*60)
            
            # Play sound alert
            try:
                for _ in range(3):
                    winsound.Beep(1000, 500)
                    time.sleep(0.2)
            except:
                pass
                
        else:
            priority = "MEDIUM"
            type_names = {'C17': 'Boeing C-17 Globemaster', 'F16': 'F-16 Fighting Falcon', 'A10': 'A-10 Thunderbolt II'}
            type_name = type_names.get(aircraft_type, 'Unknown Rare Aircraft')
            
            print(f"\n" + "="*50)
            print(f"RARE AIRCRAFT DETECTED")
            print(f"="*50)
        
        print(f"Type: {aircraft_type} ({type_name})")
        print(f"ICAO24: {icao24}")
        print(f"Registration: {aircraft_info['registration']}")
        print(f"Model: {aircraft_info['model']}")
        print(f"Operator: {aircraft_info['operator']}")
        print(f"Callsign: {callsign}")
        print(f"Position: {position}")
        print(f"Altitude: {altitude}")
        print(f"Priority: {priority}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"="*60)
        
        # Log to file
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'icao24': icao24,
                'type': aircraft_type,
                'name': type_name,
                'registration': aircraft_info['registration'],
                'callsign': callsign,
                'position': position,
                'altitude': altitude,
                'priority': priority
            }
            
            with open('aircraft_data/detection_log.txt', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass
        
        self.total_detections += 1
    
    async def check_aircraft(self):
        """Check for rare aircraft in live feed"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://opensky-network.org/api/states/all", timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        states = data.get('states', [])
                        
                        self.total_checks += 1
                        self.consecutive_errors = 0
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Checking {len(states)} aircraft... (Check #{self.total_checks})")
                        
                        rare_found = 0
                        new_detections = 0
                        
                        for state in states:
                            if not state or len(state) < 1:
                                continue
                            
                            icao24 = state[0].strip().lower() if state[0] else ''
                            callsign = state[1].strip() if state[1] else 'Unknown'
                            
                            # Check if this is a rare aircraft
                            if icao24 in self.rare_aircraft:
                                rare_found += 1
                                
                                # Check if we've already alerted on this aircraft recently
                                detection_key = f"{icao24}_{callsign}"
                                
                                if detection_key not in self.detected_aircraft:
                                    self.detected_aircraft.add(detection_key)
                                    new_detections += 1
                                    
                                    # Get aircraft info
                                    aircraft_info = self.aircraft_db[icao24]
                                    
                                    # Prepare position data
                                    position = f"{state[6]}, {state[5]}" if state[6] and state[5] else 'Unknown'
                                    altitude = f"{state[7]} ft" if state[7] else 'Unknown'
                                    
                                    # Alert!
                                    self.alert_detection(icao24, aircraft_info, callsign, position, altitude)
                        
                        if rare_found > 0:
                            print(f"  Active rare aircraft: {rare_found} ({new_detections} new)")
                        
                        # Clean detection cache if it gets too large
                        if len(self.detected_aircraft) > 1000:
                            self.detected_aircraft.clear()
                            print("  Detection cache cleared")
                        
                        return True
                        
                    else:
                        self.consecutive_errors += 1
                        print(f"API error: HTTP {response.status} (error {self.consecutive_errors})")
                        return False
                        
        except Exception as e:
            self.consecutive_errors += 1
            print(f"Error checking aircraft: {e} (error {self.consecutive_errors})")
            return False
    
    async def run(self):
        """Main monitoring loop"""
        
        print("RARE AIRCRAFT MONITOR")
        print("="*50)
        
        if not self.load_config_and_database():
            print("Failed to load configuration or database")
            return
        
        print(f"\nMonitoring for YOUR target aircraft:")
        print(f"  AB18: Aero Boero AB-180 (8 aircraft)")
        print(f"  VUT1: Evektor Cobra (3 aircraft)")
        print(f"Plus other rare military aircraft...")
        print(f"\nStarting live monitoring... Press Ctrl+C to stop")
        print("="*50)
        
        try:
            while True:
                success = await self.check_aircraft()
                
                if not success and self.consecutive_errors >= 5:
                    print(f"Too many errors ({self.consecutive_errors}). Stopping.")
                    break
                
                await asyncio.sleep(15)  # Check every 15 seconds
                
        except KeyboardInterrupt:
            print(f"\nMonitoring stopped by user")
        except Exception as e:
            print(f"Fatal error: {e}")
        
        print(f"\nSession summary:")
        print(f"  Total checks: {self.total_checks}")
        print(f"  Total detections: {self.total_detections}")

async def main():
    monitor = RareAircraftMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())