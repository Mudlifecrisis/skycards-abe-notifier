#!/usr/bin/env python3
"""
Enhanced Rare Aircraft Hunter using production aircraft database
Integrates with Discord bot system for real-time alerts
"""
import aiohttp
import asyncio
import json
import math
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

class EnhancedRareAircraftHunter:
    """Enhanced rare aircraft detection using OpenSky + local aircraft database"""
    
    def __init__(self):
        # OpenSky API setup
        opensky_creds = os.getenv("OPENSKY_API", "{}")
        try:
            creds = json.loads(opensky_creds)
            self.opensky_user = creds.get("clientId", "")
            self.opensky_pass = creds.get("clientSecret", "")
        except:
            self.opensky_user = ""
            self.opensky_pass = ""
            
        self.opensky_base = "https://opensky-network.org/api/states/all"
        
        # DeepSeek API setup
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base = "https://api.deepseek.com/v1/chat/completions"
        
        # Load production aircraft database
        self.aircraft_db = {}
        self.user_targets = {}
        self.rare_aircraft = {}
        self.load_aircraft_database()
        
        # Search terms storage (legacy support)
        self.search_terms = set()
        self.search_file = "rare_search_terms.json"
        self.load_search_terms()
        
        # Aircraft cache to avoid duplicate alerts
        self.seen_aircraft = {}
        
        # OAuth token cache
        self.opensky_token = None
        self.token_expires = 0
        
        # Quiet hours
        self.quiet_start = int(os.getenv("QUIET_START", "23"))
        self.quiet_end = int(os.getenv("QUIET_END", "6"))
        
        print(f"Enhanced Rare Aircraft Hunter initialized:")
        print(f"  Aircraft database: {len(self.aircraft_db):,} aircraft")
        print(f"  User targets: {len(self.user_targets)} (AB18, VUT1, KFIR)")
        print(f"  All rare aircraft: {len(self.rare_aircraft)}")
        
    def load_aircraft_database(self):
        """Load the production aircraft database"""
        try:
            db_file = "aircraft_data/production_aircraft_database.json"
            if os.path.exists(db_file):
                with open(db_file, 'r') as f:
                    db_data = json.load(f)
                
                self.aircraft_db = db_data.get('aircraft', {})
                self.user_targets = db_data.get('user_targets', {})
                self.rare_aircraft = db_data.get('rare_aircraft', {})
                
                print(f"Production aircraft database loaded successfully")
            else:
                print(f"Warning: Production database not found at {db_file}")
        except Exception as e:
            print(f"Error loading aircraft database: {e}")
    
    def load_search_terms(self):
        """Load saved search terms from file (legacy support)"""
        try:
            if os.path.exists(self.search_file):
                with open(self.search_file, 'r') as f:
                    data = json.load(f)
                    self.search_terms = set(data.get('terms', []))
                    
                    # Auto-add your target aircraft types if not present
                    target_types = {'AB18', 'VUT1', 'KFIR', 'C17', 'F16', 'A10'}
                    for aircraft_type in target_types:
                        self.search_terms.add(aircraft_type)
                    
                    self.save_search_terms()
        except Exception as e:
            print(f"Error loading search terms: {e}")
            # Set default target aircraft
            self.search_terms = {'AB18', 'VUT1', 'KFIR', 'C17', 'F16', 'A10'}
            self.save_search_terms()
    
    def save_search_terms(self):
        """Save search terms to file"""
        try:
            with open(self.search_file, 'w') as f:
                json.dump({'terms': list(self.search_terms)}, f, indent=2)
        except Exception as e:
            print(f"Error saving search terms: {e}")
    
    def is_quiet_hours(self) -> bool:
        """Check if we're in quiet hours (11 PM to 6 AM)"""
        now_hour = datetime.now().hour
        if self.quiet_start > self.quiet_end:  # Crosses midnight
            return now_hour >= self.quiet_start or now_hour < self.quiet_end
        return self.quiet_start <= now_hour < self.quiet_end
    
    async def get_aircraft_suggestions(self, term: str) -> List[str]:
        """Get aircraft name suggestions from DeepSeek"""
        if not self.deepseek_api_key:
            return []
            
        prompt = f"""You are an aviation expert helping a flight tracking enthusiast.

The user wants to search for '{term}' aircraft globally. Suggest 3-5 alternative names, 
variants, nicknames, or callsigns that might be used for this aircraft type.

Focus on:
- Official designations (F-16 vs F16)
- Military nicknames (VIPER, WARTHOG, etc.)
- Common variants (F16A, F16C, etc.)
- Alternative spellings or abbreviations

Return ONLY a comma-separated list, most common first. Example: "F-16, VIPER, FIGHTING FALCON, F16C"
No explanations, just the comma-separated list."""

        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.deepseek_base, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        suggestions_text = data['choices'][0]['message']['content'].strip()
                        suggestions = [s.strip().upper() for s in suggestions_text.split(',')]
                        return [s for s in suggestions if s and len(s) > 1]
                    else:
                        print(f"DeepSeek API error: {response.status}")
                        return []
        except Exception as e:
            print(f"DeepSeek suggestion error: {e}")
            return []
    
    def add_search_term(self, term: str):
        """Add a search term"""
        term = term.upper().strip()
        self.search_terms.add(term)
        self.save_search_terms()
    
    def remove_search_term(self, term: str):
        """Remove a search term"""
        term = term.upper().strip()
        self.search_terms.discard(term)
        self.save_search_terms()
    
    def get_search_terms(self) -> List[str]:
        """Get all search terms"""
        return sorted(list(self.search_terms))
    
    def clear_search_terms(self):
        """Clear all search terms"""
        self.search_terms.clear()
        self.save_search_terms()
    
    async def _get_opensky_token(self) -> Optional[str]:
        """Get OAuth2 token for OpenSky API"""
        import time
        
        # Return cached token if still valid
        if self.opensky_token and time.time() < self.token_expires:
            return self.opensky_token
            
        try:
            token_url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.opensky_user,
                "client_secret": self.opensky_pass
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data, timeout=30) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.opensky_token = token_data["access_token"]
                        # Token expires in 30 minutes, refresh 5 minutes early
                        self.token_expires = time.time() + (token_data.get("expires_in", 1800) - 300)
                        print("OpenSky OAuth token obtained successfully")
                        return self.opensky_token
                    else:
                        print(f"Failed to get OpenSky token: {response.status}")
                        return None
        except Exception as e:
            print(f"Error getting OpenSky token: {e}")
            return None
    
    async def fetch_global_aircraft(self) -> List[Dict]:
        """Fetch all current aircraft positions from OpenSky Network"""
        try:
            # Try with OAuth2 authentication first
            if self.opensky_user and self.opensky_pass:
                token = await self._get_opensky_token()
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(self.opensky_base, headers=headers, timeout=30) as response:
                            if response.status == 200:
                                data = await response.json()
                                return self._parse_opensky_data(data)
                            elif response.status == 401:
                                print("OpenSky authentication failed, trying anonymous access...")
                            else:
                                print(f"OpenSky API error with auth: {response.status}")
            
            # Fall back to anonymous access
            async with aiohttp.ClientSession() as session:
                async with session.get(self.opensky_base, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_opensky_data(data)
                    else:
                        print(f"OpenSky API error (anonymous): {response.status}")
                        return []
        except Exception as e:
            print(f"OpenSky API error: {e}")
            return []

    def _parse_opensky_data(self, data: Dict) -> List[Dict]:
        """Convert OpenSky state vectors to our aircraft format"""
        if not data or 'states' not in data or data['states'] is None:
            return []
            
        aircraft_list = []
        for state in data['states']:
            if not state or len(state) < 17:
                continue
                
            # Skip aircraft with no position
            if state[5] is None or state[6] is None:
                continue
                
            aircraft = {
                'icao24': state[0] or '',
                'callsign': (state[1] or '').strip().upper(),
                'origin_country': state[2] or '',
                'longitude': state[5],
                'latitude': state[6], 
                'altitude': state[7],  # meters
                'velocity': state[9],  # m/s
                'heading': state[10],
                'vertical_rate': state[11],
                'last_contact': state[4],
                'detected_at': datetime.now(timezone.utc).isoformat()
            }
            
            aircraft_list.append(aircraft)
            
        return aircraft_list

    def matches_database(self, aircraft: Dict) -> Tuple[bool, str, str]:
        """Check if aircraft matches our database (PRIMARY METHOD)"""
        icao24 = aircraft.get('icao24', '').lower()
        
        # Check if this ICAO24 is in our aircraft database
        if icao24 in self.aircraft_db:
            aircraft_info = self.aircraft_db[icao24]
            aircraft_type = aircraft_info.get('type', '').upper()
            
            # Check if this is a rare aircraft
            if icao24 in self.rare_aircraft:
                return True, aircraft_type, f"Database: {aircraft_type}"
            
            # Check if this matches our search terms
            if aircraft_type in self.search_terms:
                return True, aircraft_type, f"Search: {aircraft_type}"
        
        return False, "", ""

    def matches_search_terms(self, aircraft: Dict) -> Tuple[bool, str]:
        """Check if aircraft matches search terms (LEGACY METHOD)"""
        if not self.search_terms:
            return False, ""
            
        callsign = aircraft.get('callsign', '').upper()
        icao24 = aircraft.get('icao24', '').upper()
        country = aircraft.get('origin_country', '').upper()
        
        # Check all search terms against aircraft data
        for term in self.search_terms:
            # For ICAO codes (like B35, KC135), only match callsign prefixes
            if len(term) <= 6 and term.isalnum():
                if callsign.startswith(term):
                    return True, term
            else:
                # For longer terms, check callsign and country
                if (term in callsign or term in country):
                    return True, term
                
        return False, ""

    def is_duplicate_alert(self, aircraft: Dict, matched_term: str) -> bool:
        """Check if we've already alerted for this aircraft recently or if it's ghost data"""
        icao24 = aircraft.get('icao24', '')
        callsign = aircraft.get('callsign', '')
        key = f"{icao24}_{callsign}_{matched_term}"
        now = datetime.now(timezone.utc)
        
        # Get current position data
        current_lat = aircraft.get('latitude')
        current_lon = aircraft.get('longitude') 
        current_alt = aircraft.get('altitude')
        current_speed = aircraft.get('velocity')
        
        if key in self.seen_aircraft:
            last_seen = datetime.fromisoformat(self.seen_aircraft[key]['last_alert'])
            last_aircraft = self.seen_aircraft[key].get('aircraft', {})
            
            # Check for ghost aircraft - same exact position for 10+ minutes
            if (current_lat and current_lon and current_alt is not None and 
                last_aircraft.get('latitude') == current_lat and
                last_aircraft.get('longitude') == current_lon and 
                last_aircraft.get('altitude') == current_alt and
                (now - last_seen).total_seconds() > 600):  # 10 minutes same position
                print(f"Skipping ghost aircraft {callsign} - same position for {(now - last_seen).total_seconds()/60:.1f} minutes")
                return True
                
            # Don't re-alert for same aircraft/term within 30 minutes  
            if (now - last_seen).total_seconds() < 1800:  # 30 minutes
                return True
        
        # Additional ghost detection - very low altitude + low speed likely stale
        if (current_alt is not None and current_speed is not None and 
            current_alt < 914 and current_speed < 25.7):  # <3000ft and <50kts 
            print(f"Skipping likely stale aircraft {callsign} - low altitude ({current_alt*3.28:.0f}ft) and slow speed ({current_speed*1.94:.0f}kts)")
            return True
        
        # Update cache with current position
        self.seen_aircraft[key] = {
            'last_alert': now.isoformat(),
            'aircraft': aircraft,
            'term': matched_term
        }
        
        return False

    async def find_rare_aircraft(self) -> List[Dict]:
        """Find aircraft matching our database and search terms"""
        if self.is_quiet_hours():
            return []
            
        all_aircraft = await self.fetch_global_aircraft()
        rare_finds = []
        
        print(f"Scanning {len(all_aircraft)} live aircraft for rare types...")
        
        database_matches = 0
        search_matches = 0
        
        for aircraft in all_aircraft:
            icao24 = aircraft.get('icao24', '').lower()
            
            # METHOD 1: Check database first (most accurate)
            is_db_match, aircraft_type, db_reason = self.matches_database(aircraft)
            
            if is_db_match:
                database_matches += 1
                
                if not self.is_duplicate_alert(aircraft, aircraft_type):
                    # Get full aircraft info from database
                    aircraft_info = self.aircraft_db.get(icao24, {})
                    
                    # Enhance aircraft data
                    aircraft['matched_term'] = aircraft_type
                    aircraft['search_reason'] = db_reason
                    aircraft['aircraft_info'] = aircraft_info
                    aircraft['registration'] = aircraft_info.get('registration', 'Unknown')
                    aircraft['model'] = aircraft_info.get('model', 'Unknown')
                    aircraft['manufacturer'] = aircraft_info.get('manufacturer', 'Unknown')
                    aircraft['operator'] = aircraft_info.get('operator', 'Unknown')
                    
                    # Check if this is a user target aircraft
                    if icao24 in self.user_targets:
                        aircraft['is_user_target'] = True
                        aircraft['priority'] = 'HIGH'
                    else:
                        aircraft['is_user_target'] = False
                        aircraft['priority'] = 'MEDIUM'
                    
                    # Add display info
                    if aircraft.get('altitude'):
                        aircraft['altitude_ft'] = int(aircraft['altitude'] * 3.28084)
                    if aircraft.get('velocity'):
                        aircraft['velocity_kts'] = int(aircraft['velocity'] * 1.944)
                    
                    rare_finds.append(aircraft)
                    continue
            
            # METHOD 2: Legacy text matching for callsigns
            is_text_match, matched_term = self.matches_search_terms(aircraft)
            
            if is_text_match and not self.is_duplicate_alert(aircraft, matched_term):
                search_matches += 1
                
                aircraft['matched_term'] = matched_term
                aircraft['search_reason'] = f"Callsign search: {matched_term}"
                aircraft['aircraft_info'] = {}
                aircraft['registration'] = 'Unknown'
                aircraft['model'] = 'Unknown'
                aircraft['manufacturer'] = 'Unknown'
                aircraft['operator'] = 'Unknown'
                aircraft['is_user_target'] = False
                aircraft['priority'] = 'LOW'
                
                # Add display info
                if aircraft.get('altitude'):
                    aircraft['altitude_ft'] = int(aircraft['altitude'] * 3.28084)
                if aircraft.get('velocity'):
                    aircraft['velocity_kts'] = int(aircraft['velocity'] * 1.944)
                
                rare_finds.append(aircraft)
        
        if rare_finds:
            print(f"Found {len(rare_finds)} rare aircraft:")
            print(f"  Database matches: {database_matches}")
            print(f"  Search matches: {search_matches}")
            
            # Show user target aircraft first
            user_targets_found = [a for a in rare_finds if a.get('is_user_target', False)]
            if user_targets_found:
                print(f"  USER TARGET AIRCRAFT: {len(user_targets_found)}")
                for aircraft in user_targets_found:
                    print(f"    {aircraft['matched_term']}: {aircraft['callsign']} ({aircraft['registration']})")
        
        return rare_finds

    def get_statistics(self) -> Dict:
        """Get hunter statistics"""
        return {
            'database_aircraft': len(self.aircraft_db),
            'user_targets': len(self.user_targets),
            'rare_aircraft': len(self.rare_aircraft),
            'search_terms': len(self.search_terms),
            'seen_aircraft': len(self.seen_aircraft)
        }

# Backward compatibility - replace the old class
class RareAircraftHunter(EnhancedRareAircraftHunter):
    """Backward compatible wrapper"""
    pass