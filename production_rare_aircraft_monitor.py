#!/usr/bin/env python3
"""
Production Rare Aircraft Monitor - 24/7 monitoring service
"""
import asyncio
import aiohttp
import json
import os
import time
import winsound  # For Windows sound alerts
from datetime import datetime, timedelta
import logging

class ProductionAircraftMonitor:
    def __init__(self, config_file="aircraft_data/monitoring_config.json"):
        self.config_file = config_file
        self.config = None
        self.aircraft_db = {}
        self.user_targets = {}
        self.rare_aircraft = {}
        self.detected_aircraft = set()  # Track what we've already alerted on
        self.consecutive_errors = 0
        self.last_check_time = None
        self.total_checks = 0
        self.total_detections = 0
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('aircraft_data/monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load monitoring configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Configuration loaded from {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return False
    
    def load_aircraft_database(self):
        """Load the production aircraft database"""
        
        if not self.config:
            self.logger.error("No configuration loaded")
            return False
            
        db_file = self.config['monitoring']['database_file']
        
        try:
            self.logger.info(f"Loading aircraft database from {db_file}...")
            
            with open(db_file, 'r') as f:
                db_data = json.load(f)
            
            self.aircraft_db = db_data['aircraft']
            self.user_targets = db_data['user_targets']
            self.rare_aircraft = db_data['rare_aircraft']
            
            self.logger.info(f"Database loaded successfully:")
            self.logger.info(f"  Total aircraft: {len(self.aircraft_db):,}")
            self.logger.info(f"  Your target aircraft: {len(self.user_targets)}")
            self.logger.info(f"  All rare aircraft: {len(self.rare_aircraft)}")
            
            # Show your specific target aircraft
            target_by_type = {}
            for icao24, info in self.user_targets.items():
                aircraft_type = info['type']
                if aircraft_type not in target_by_type:
                    target_by_type[aircraft_type] = []
                target_by_type[aircraft_type].append((icao24, info))
            
            self.logger.info("Your target aircraft loaded:")
            for aircraft_type, aircraft_list in target_by_type.items():
                type_name = self.config['target_aircraft'][aircraft_type]['name']
                self.logger.info(f"  {aircraft_type} ({type_name}): {len(aircraft_list)} aircraft")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading aircraft database: {e}")
            return False
    
    def play_alert_sound(self, priority="HIGH"):
        """Play alert sound for detections"""
        try:
            if priority == "HIGH":
                # High priority - multiple beeps
                for _ in range(3):
                    winsound.Beep(1000, 500)  # 1000Hz for 500ms
                    time.sleep(0.2)
            else:
                # Medium priority - single beep
                winsound.Beep(800, 300)  # 800Hz for 300ms
        except Exception as e:
            self.logger.warning(f"Could not play sound alert: {e}")
    
    def log_detection(self, aircraft_info, live_data):
        """Log aircraft detection to file"""
        
        if not self.config['notifications']['log_to_file']:
            return
            
        try:
            log_file = self.config['notifications']['log_file']
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'icao24': aircraft_info['icao24'],
                'type': aircraft_info['type'],
                'name': aircraft_info['name'],
                'registration': aircraft_info['registration'],
                'callsign': live_data['callsign'],
                'position': live_data['position'],
                'altitude': live_data['altitude'],
                'priority': aircraft_info['priority']
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            self.logger.warning(f"Could not log detection: {e}")
    
    def alert_rare_aircraft(self, icao24, aircraft_info, live_data):
        """Handle rare aircraft detection and alerting"""
        
        aircraft_type = aircraft_info['type']
        
        # Determine if this is user target or other rare
        if aircraft_type in self.config['target_aircraft']:
            config_info = self.config['target_aircraft'][aircraft_type]
            is_user_target = True
        else:
            config_info = self.config['other_rare_aircraft'].get(aircraft_type, {})
            is_user_target = False
        
        priority = config_info.get('priority', 'MEDIUM')
        should_notify = config_info.get('notify', True)
        should_sound = config_info.get('sound_alert', False)
        
        if not should_notify:
            return
        
        # Create alert message
        alert_msg = f"\n{'='*60}\n"
        if is_user_target:
            alert_msg += "🚨 YOUR TARGET RARE AIRCRAFT DETECTED! 🚨\n"
        else:
            alert_msg += "✈️  RARE AIRCRAFT DETECTED\n"
        
        alert_msg += f"{'='*60}\n"
        alert_msg += f"Type: {aircraft_type} ({config_info.get('name', 'Unknown')})\n"
        alert_msg += f"ICAO24: {icao24}\n"
        alert_msg += f"Registration: {aircraft_info['registration']}\n"
        alert_msg += f"Model: {aircraft_info['model']}\n"
        alert_msg += f"Operator: {aircraft_info['operator']}\n"
        alert_msg += f"Callsign: {live_data['callsign']}\n"
        alert_msg += f"Position: {live_data['position']}\n"
        alert_msg += f"Altitude: {live_data['altitude']}\n"
        alert_msg += f"Priority: {priority}\n"
        alert_msg += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        alert_msg += f"{'='*60}\n"
        
        # Log the alert
        self.logger.info(alert_msg)
        print(alert_msg)  # Also print to console for immediate visibility
        
        # Play sound alert
        if should_sound and self.config['notifications']['sound_alerts']:
            self.play_alert_sound(priority)
        
        # Log to detection file
        detection_info = {
            'icao24': icao24,
            'type': aircraft_type,
            'name': config_info.get('name', 'Unknown'),
            'registration': aircraft_info['registration'],
            'priority': priority
        }
        
        self.log_detection(detection_info, live_data)
        self.total_detections += 1
    
    async def check_live_aircraft(self):
        """Check OpenSky live feed for rare aircraft"""
        
        try:
            async with aiohttp.ClientSession() as session:
                timeout = self.config['monitoring']['api_timeout_seconds']
                
                async with session.get("https://opensky-network.org/api/states/all", timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        states = data.get('states', [])
                        
                        self.last_check_time = datetime.now()
                        self.total_checks += 1
                        self.consecutive_errors = 0  # Reset error counter
                        
                        timestamp = self.last_check_time.strftime("%H:%M:%S")
                        self.logger.info(f"[{timestamp}] Checking {len(states)} live aircraft... (Check #{self.total_checks})")
                        
                        rare_found = 0
                        new_detections = 0
                        
                        for state in states:
                            if not state or len(state) < 1:
                                continue
                            
                            icao24 = state[0].strip().lower() if state[0] else ''
                            callsign = state[1].strip() if state[1] else 'Unknown'
                            
                            # Check if this aircraft is in our database
                            if icao24 in self.aircraft_db:
                                aircraft_info = self.aircraft_db[icao24]
                                aircraft_type = aircraft_info['type']
                                
                                # Check if this is a rare aircraft
                                if icao24 in self.rare_aircraft:
                                    rare_found += 1
                                    
                                    # Create unique detection key
                                    detection_key = f"{icao24}_{callsign}_{timestamp[:5]}"  # Include time to detect re-appearances
                                    
                                    if detection_key not in self.detected_aircraft:
                                        self.detected_aircraft.add(detection_key)
                                        new_detections += 1
                                        
                                        # Prepare live data
                                        live_data = {
                                            'callsign': callsign,
                                            'position': f"{state[6]}, {state[5]}" if state[6] and state[5] else 'Unknown',
                                            'altitude': f"{state[7]} ft" if state[7] else 'Unknown'
                                        }
                                        
                                        # Alert on this rare aircraft
                                        self.alert_rare_aircraft(icao24, aircraft_info, live_data)
                        
                        if rare_found > 0:
                            self.logger.info(f"  Active rare aircraft: {rare_found} ({new_detections} new detections)")
                        
                        return True
                        
                    else:
                        self.consecutive_errors += 1
                        self.logger.warning(f"API error: HTTP {response.status} (error {self.consecutive_errors})")
                        return False
                        
        except Exception as e:
            self.consecutive_errors += 1
            self.logger.error(f"Error checking live aircraft: {e} (error {self.consecutive_errors})")
            return False
    
    async def run_monitoring(self):
        """Main monitoring loop"""
        
        self.logger.info("Starting Production Rare Aircraft Monitor")
        self.logger.info("=" * 60)
        
        # Load configuration and database
        if not self.load_config():
            self.logger.error("Failed to load configuration. Exiting.")
            return
            
        if not self.load_aircraft_database():
            self.logger.error("Failed to load aircraft database. Exiting.")
            return
        
        check_interval = self.config['monitoring']['check_interval_seconds']
        max_errors = self.config['monitoring']['max_consecutive_errors']
        
        self.logger.info(f"Monitor configured:")
        self.logger.info(f"  Check interval: {check_interval} seconds")
        self.logger.info(f"  Max consecutive errors: {max_errors}")
        self.logger.info(f"  Target aircraft: {len(self.user_targets)}")
        
        self.logger.info("\nStarting live monitoring... Press Ctrl+C to stop")
        print("\n" + "="*60)
        print("🔍 RARE AIRCRAFT MONITOR ACTIVE")
        print("="*60)
        print("Watching for your target aircraft:")
        print("  AB18: Aero Boero AB-180 (8 aircraft)")
        print("  VUT1: Evektor Cobra (3 aircraft)")
        print("Plus other rare military aircraft...")
        print("="*60)
        
        try:
            while True:
                success = await self.check_live_aircraft()
                
                if not success:
                    if self.consecutive_errors >= max_errors:
                        self.logger.error(f"Too many consecutive errors ({self.consecutive_errors}). Stopping monitor.")
                        break
                
                # Clean up old detections (remove entries older than 1 hour)
                if len(self.detected_aircraft) > 1000:
                    self.detected_aircraft.clear()
                    self.logger.info("Cleared detection cache")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\nMonitoring stopped by user")
        
        except Exception as e:
            self.logger.error(f"Fatal error in monitoring loop: {e}")
        
        finally:
            self.logger.info(f"Monitor session summary:")
            self.logger.info(f"  Total checks: {self.total_checks}")
            self.logger.info(f"  Total detections: {self.total_detections}")
            self.logger.info(f"  Runtime: {datetime.now() - (self.last_check_time or datetime.now())}")

async def main():
    """Main function"""
    monitor = ProductionAircraftMonitor()
    await monitor.run_monitoring()

if __name__ == "__main__":
    asyncio.run(main())