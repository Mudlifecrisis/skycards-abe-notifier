# rare_hunter.py
import aiohttp
import asyncio
import json
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

class RareAircraftHunter:
    """Global rare aircraft detection using OpenSky Network API"""
    
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
        
        # Search terms storage
        self.search_terms = set()
        self.search_file = "rare_search_terms.json"
        self.load_search_terms()
        
        # Aircraft cache to avoid duplicate alerts
        self.seen_aircraft = {}
        
        # Quiet hours (use environment variables, fallback to 23-6)
        self.quiet_start = int(os.getenv("QUIET_START", "23"))
        self.quiet_end = int(os.getenv("QUIET_END", "6"))
        
    def load_search_terms(self):
        """Load saved search terms from file"""
        try:
            if os.path.exists(self.search_file):
                with open(self.search_file, 'r') as f:
                    data = json.load(f)
                    self.search_terms = set(data.get('terms', []))
        except Exception as e:
            print(f"Error loading search terms: {e}")
            self.search_terms = set()
    
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
    
    async def fetch_global_aircraft(self) -> List[Dict]:
        """Fetch all current aircraft positions from OpenSky Network"""
        try:
            # Try with authentication first
            if self.opensky_user and self.opensky_pass:
                auth = aiohttp.BasicAuth(self.opensky_user, self.opensky_pass)
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.opensky_base, auth=auth, timeout=30) as response:
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
        if not data or 'states' not in data:
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

    def matches_search_terms(self, aircraft: Dict) -> Tuple[bool, str]:
        """Check if aircraft matches any search terms"""
        if not self.search_terms:
            return False, ""
            
        callsign = aircraft.get('callsign', '').upper()
        icao24 = aircraft.get('icao24', '').upper()
        country = aircraft.get('origin_country', '').upper()
        
        # Check all search terms against aircraft data
        for term in self.search_terms:
            # For ICAO codes (like B35, KC135), only match callsign prefixes
            # Don't match random ICAO24 hex codes
            if len(term) <= 6 and term.isalnum():
                # This is likely an aircraft type code - only match callsign
                if callsign.startswith(term):
                    return True, term
            else:
                # For longer terms (like STRATOTANKER), check callsign and country
                if (term in callsign or term in country):
                    return True, term
                
        return False, ""

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def is_duplicate_alert(self, aircraft: Dict, matched_term: str) -> bool:
        """Check if we've already alerted for this aircraft recently"""
        key = f"{aircraft['icao24']}_{matched_term}"
        now = datetime.now(timezone.utc)
        
        if key in self.seen_aircraft:
            last_seen = datetime.fromisoformat(self.seen_aircraft[key]['last_alert'])
            # Don't re-alert for same aircraft/term within 30 minutes
            if (now - last_seen).total_seconds() < 1800:  # 30 minutes
                return True
        
        # Update cache
        self.seen_aircraft[key] = {
            'last_alert': now.isoformat(),
            'aircraft': aircraft,
            'term': matched_term
        }
        
        return False

    async def find_rare_aircraft(self) -> List[Dict]:
        """Find aircraft matching search terms"""
        if not self.search_terms:
            return []
            
        if self.is_quiet_hours():
            return []
            
        all_aircraft = await self.fetch_global_aircraft()
        rare_finds = []
        
        for aircraft in all_aircraft:
            is_match, matched_term = self.matches_search_terms(aircraft)
            
            if is_match and not self.is_duplicate_alert(aircraft, matched_term):
                # Add search context
                aircraft['matched_term'] = matched_term
                aircraft['search_reason'] = f"Matched search term: {matched_term}"
                
                # Add altitude in feet for display
                if aircraft.get('altitude'):
                    aircraft['altitude_ft'] = int(aircraft['altitude'] * 3.28084)
                
                # Add speed in knots for display  
                if aircraft.get('velocity'):
                    aircraft['velocity_kts'] = int(aircraft['velocity'] * 1.944)
                
                rare_finds.append(aircraft)
        
        return rare_finds

    async def get_airport_arrivals(self, airport_iata: str) -> List[Dict]:
        """Get aircraft approaching an airport (basic implementation with OpenSky)"""
        # This is a simplified version - OpenSky doesn't have arrival data
        # We'll look for aircraft near the airport coordinates
        
        # Airport coordinates (you'd want a proper airport database)
        airport_coords = {
            'ABE': (40.6520, -75.4398),  # Allentown
            'JFK': (40.6413, -73.7781),
            'LAX': (33.9425, -118.4081),
            'ORD': (41.9742, -87.9073),
        }
        
        if airport_iata.upper() not in airport_coords:
            return []
            
        airport_lat, airport_lon = airport_coords[airport_iata.upper()]
        
        all_aircraft = await self.fetch_global_aircraft()
        nearby_aircraft = []
        
        for aircraft in all_aircraft:
            distance = self.calculate_distance(
                airport_lat, airport_lon,
                aircraft['latitude'], aircraft['longitude']
            )
            
            # Aircraft within 50km of airport, flying below 10,000 feet
            if (distance < 50 and 
                aircraft.get('altitude', 0) and aircraft['altitude'] < 3048):  # 10k feet in meters
                
                aircraft['distance_to_airport'] = round(distance, 1)
                aircraft['airport'] = airport_iata.upper()
                nearby_aircraft.append(aircraft)
        
        return nearby_aircraft