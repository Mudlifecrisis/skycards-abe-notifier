#!/usr/bin/env python3
"""
RESCUE VERSION - Simplified Rare Aircraft Hunter
Uses anonymous OpenSky + exact type matching with local DB
No OAuth complexity, just works.
"""
import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

class RareAircraftHunter:
    """Simplified rare aircraft detection - anonymous OpenSky + exact type matching"""
    
    def __init__(self):
        # Anonymous OpenSky only - no OAuth complexity
        self.opensky_base = "https://opensky-network.org/api/states/all"
        
        # Load aircraft database (normalized keys)
        self.aircraft_db = {}
        self.load_aircraft_database()
        
        # Search terms with human aliases
        self.search_terms = set()
        self.search_file = "rare_search_terms.json" 
        self.load_search_terms()
        
        # Simple duplicate tracking
        self.seen_aircraft = {}
        
        # Quiet hours
        self.quiet_start = int(os.getenv("QUIET_START", "23"))
        self.quiet_end = int(os.getenv("QUIET_END", "6"))
        
        print(f"[RESCUE] Rare Aircraft Hunter initialized")
        print(f"  aircraft_db_size={len(self.aircraft_db)}")
        print(f"  search_terms={sorted(list(self.search_terms))}")
        
    # Human-readable aliases to type codes
    ALIASES = {
        "globemaster": {"C17"},
        "chinook": {"H47"},
        "a10": {"A10"}, 
        "f16": {"F16"},
        "stratolifter": {"C135"},
        "aero boero ab-180": {"AB18"},
        "evektor cobra": {"VUT1"},
        "travel air 5": {"AA5", "TVL4", "TVLB"}
    }
    
    def norm_hex(self, x: str) -> str:
        """Normalize ICAO24 hex identifier"""
        return x.strip().lower() if x else ""
        
    def norm_type(self, x: str) -> str:
        """Normalize aircraft type code"""
        return x.strip().upper() if x else ""

    def load_aircraft_database(self):
        """Load production aircraft database with normalized keys"""
        try:
            db_file = "aircraft_data/production_aircraft_database.json"
            if os.path.exists(db_file):
                with open(db_file, 'r') as f:
                    raw_data = json.load(f)
                
                # Handle both old and new format
                if 'aircraft' in raw_data:
                    raw_aircraft = raw_data['aircraft'] 
                else:
                    raw_aircraft = raw_data
                
                # Normalize all keys and type codes
                self.aircraft_db = {}
                for icao24, info in raw_aircraft.items():
                    norm_icao = self.norm_hex(icao24)
                    if norm_icao and info:
                        # Normalize type codes
                        if 'type' in info:
                            info['type'] = self.norm_type(info['type'])
                        if 'icao_type' in info:
                            info['icao_type'] = self.norm_type(info['icao_type'])
                        
                        self.aircraft_db[norm_icao] = info
                        
                print(f"[RESCUE] Aircraft database loaded: {len(self.aircraft_db):,} aircraft")
            else:
                print(f"[ERROR] Database not found: {db_file}")
        except Exception as e:
            print(f"[ERROR] Loading aircraft database: {e}")
    
    def load_search_terms(self):
        """Load search terms - convert aliases to type codes"""
        try:
            if os.path.exists(self.search_file):
                with open(self.search_file, 'r') as f:
                    data = json.load(f)
                    raw_terms = data.get('terms', [])
            else:
                raw_terms = []
            
            # Default targets
            if not raw_terms:
                raw_terms = ["globemaster", "chinook", "a10", "f16", "aero boero ab-180", "evektor cobra"]
            
            # Convert human terms to type codes
            self.search_terms = set()
            for term in raw_terms:
                term_lower = term.lower().strip()
                if term_lower in self.ALIASES:
                    # Add all type codes for this alias
                    self.search_terms.update(self.ALIASES[term_lower])
                else:
                    # Treat as direct type code
                    self.search_terms.add(self.norm_type(term))
            
            # Always include user targets
            self.search_terms.update(["AB18", "VUT1", "KFIR"])
            
            print(f"[RESCUE] Search terms loaded: {sorted(list(self.search_terms))}")
            self.save_search_terms()
            
        except Exception as e:
            print(f"[ERROR] Loading search terms: {e}")
            self.search_terms = {"C17", "H47", "A10", "F16", "AB18", "VUT1", "KFIR"}

    def save_search_terms(self):
        """Save current search terms"""
        try:
            with open(self.search_file, 'w') as f:
                json.dump({'terms': sorted(list(self.search_terms))}, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Saving search terms: {e}")

    def add_search_term(self, term: str):
        """Add search term - handle aliases"""
        term_lower = term.lower().strip()
        if term_lower in self.ALIASES:
            self.search_terms.update(self.ALIASES[term_lower])
            print(f"[RESCUE] Added alias '{term}' -> {self.ALIASES[term_lower]}")
        else:
            self.search_terms.add(self.norm_type(term))
            print(f"[RESCUE] Added type code: {self.norm_type(term)}")
        self.save_search_terms()
    
    def remove_search_term(self, term: str):
        """Remove search term"""
        term_lower = term.lower().strip()
        if term_lower in self.ALIASES:
            for type_code in self.ALIASES[term_lower]:
                self.search_terms.discard(type_code)
        else:
            self.search_terms.discard(self.norm_type(term))
        self.save_search_terms()
    
    def get_search_terms(self) -> List[str]:
        """Get current search terms"""
        return sorted(list(self.search_terms))

    def is_quiet_hours(self) -> bool:
        """Check if in quiet hours"""
        now_hour = datetime.now().hour
        if self.quiet_start > self.quiet_end:  # Crosses midnight
            return now_hour >= self.quiet_start or now_hour < self.quiet_end
        return self.quiet_start <= now_hour < self.quiet_end

    async def fetch_global_aircraft(self) -> List[Dict]:
        """Fetch aircraft from OpenSky - ANONYMOUS ONLY"""
        try:
            print("[RESCUE] Fetching from OpenSky (anonymous)...")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.opensky_base, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        aircraft = self._parse_opensky_data(data)
                        print(f"[RESCUE] states_pulled={len(aircraft)}")
                        return aircraft
                    else:
                        print(f"[ERROR] OpenSky API: {response.status}")
                        return []
        except Exception as e:
            print(f"[ERROR] OpenSky fetch: {e}")
            return []

    def _parse_opensky_data(self, data: Dict) -> List[Dict]:
        """Convert OpenSky states to aircraft dicts"""
        if not data or 'states' not in data or data['states'] is None:
            return []
            
        aircraft_list = []
        for state in data['states']:
            if not state or len(state) < 17:
                continue
                
            # Skip aircraft without position
            if state[5] is None or state[6] is None:
                continue
                
            aircraft = {
                'icao24': self.norm_hex(state[0] or ''),
                'callsign': (state[1] or '').strip().upper(),
                'origin_country': state[2] or '',
                'longitude': state[5],
                'latitude': state[6], 
                'altitude': state[7],  # meters
                'velocity': state[9],  # m/s
                'heading': state[10],
                'last_contact': state[4],
                'detected_at': datetime.now(timezone.utc).isoformat()
            }
            
            aircraft_list.append(aircraft)
            
        return aircraft_list

    def is_duplicate_alert(self, aircraft: Dict, matched_type: str) -> bool:
        """Simple duplicate detection - 10 minutes same position = ghost"""
        icao24 = aircraft.get('icao24', '')
        key = f"{icao24}_{matched_type}"
        now = datetime.now(timezone.utc)
        
        current_lat = aircraft.get('latitude')
        current_lon = aircraft.get('longitude')
        
        if key in self.seen_aircraft:
            last_seen = datetime.fromisoformat(self.seen_aircraft[key]['last_alert'])
            last_aircraft = self.seen_aircraft[key].get('aircraft', {})
            
            # Ghost detection: same position for 10+ minutes
            if (current_lat and current_lon and 
                last_aircraft.get('latitude') == current_lat and
                last_aircraft.get('longitude') == current_lon and 
                (now - last_seen).total_seconds() > 600):
                print(f"[GHOST] Skipping {aircraft.get('callsign')} - same position {(now - last_seen).total_seconds()/60:.1f}min")
                return True
                
            # Don't re-alert within 30 minutes  
            if (now - last_seen).total_seconds() < 1800:
                return True
        
        # Update cache
        self.seen_aircraft[key] = {
            'last_alert': now.isoformat(),
            'aircraft': aircraft,
            'type': matched_type
        }
        
        return False

    async def find_rare_aircraft(self) -> List[Dict]:
        """CORE RESCUE LOOP - Anonymous OpenSky + exact type matching"""
        if self.is_quiet_hours():
            print("[RESCUE] Quiet hours - skipping")
            return []
            
        # Step 1: Get live states
        live_aircraft = await self.fetch_global_aircraft()
        if not live_aircraft:
            print("[ERROR] No aircraft data received")
            return []
        
        # Step 2: Extract ICAO24s for database lookup
        icao24s = {a['icao24'] for a in live_aircraft}
        print(f"[RESCUE] icao24s_extracted={len(icao24s)}")
        
        # Step 3: Join live data with local database
        resolved = []
        for aircraft in live_aircraft:
            icao24 = aircraft['icao24']
            if icao24 in self.aircraft_db:
                db_info = self.aircraft_db[icao24]
                # Merge live + database info
                aircraft.update({
                    'db_type': db_info.get('type', '') or db_info.get('icao_type', ''),
                    'registration': db_info.get('registration', 'Unknown'),
                    'model': db_info.get('model', 'Unknown'),
                    'manufacturer': db_info.get('manufacturer', 'Unknown')
                })
                resolved.append(aircraft)
        
        print(f"[RESCUE] resolved={len(resolved)}")
        
        # Step 4: Exact type matching
        target_types = self.search_terms
        hits = []
        for aircraft in resolved:
            db_type = aircraft.get('db_type', '')
            if db_type in target_types:
                hits.append(aircraft)
        
        print(f"[RESCUE] matched={len(hits)} target_types={sorted(list(target_types))}")
        
        # Step 5: Filter duplicates/ghosts
        rare_finds = []
        for aircraft in hits:
            matched_type = aircraft['db_type']
            if not self.is_duplicate_alert(aircraft, matched_type):
                # Add display fields
                aircraft['matched_term'] = matched_type
                aircraft['search_reason'] = f"DB exact match: {matched_type}"
                aircraft['is_user_target'] = matched_type in ['AB18', 'VUT1', 'KFIR']
                aircraft['priority'] = 'HIGH' if aircraft['is_user_target'] else 'MEDIUM'
                
                # Convert altitude/velocity to display units
                if aircraft.get('altitude'):
                    aircraft['altitude_ft'] = int(aircraft['altitude'] * 3.28084)
                if aircraft.get('velocity'):
                    aircraft['velocity_kts'] = int(aircraft['velocity'] * 1.944)
                
                rare_finds.append(aircraft)
        
        # Final logging
        if rare_finds:
            print(f"[SUCCESS] alerts_sent={len(rare_finds)}")
            for aircraft in rare_finds:
                print(f"  -> {aircraft['matched_term']}: {aircraft['callsign']} ({aircraft['registration']})")
        else:
            print(f"[RESCUE] No rare aircraft found this cycle")
            if resolved:
                # Show what types we saw but didn't match
                seen_types = set()
                for a in resolved[:10]:  # Sample first 10
                    if a.get('db_type'):
                        seen_types.add(a['db_type'])
                print(f"  Sample types seen: {sorted(list(seen_types))[:5]}")
        
        return rare_finds

    def get_statistics(self) -> Dict:
        """Get hunter statistics"""
        return {
            'database_aircraft': len(self.aircraft_db),
            'search_terms': len(self.search_terms),
            'seen_aircraft': len(self.seen_aircraft),
            'target_types': sorted(list(self.search_terms))
        }

# For testing
async def test_rescue():
    """Test the rescue version"""
    hunter = RareAircraftHunter()
    print(f"\n[TEST] Starting rare aircraft hunt...")
    results = await hunter.find_rare_aircraft()
    print(f"[TEST] Found {len(results)} rare aircraft")
    print(f"[TEST] Statistics: {hunter.get_statistics()}")

if __name__ == "__main__":
    asyncio.run(test_rescue())