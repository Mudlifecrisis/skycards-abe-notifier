#!/usr/bin/env python3
"""
Mission Finder - Find flights meeting specific mission criteria near airports
"""
import aiohttp
import asyncio
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import os
import json
from dotenv import load_dotenv

load_dotenv()

class MissionFinder:
    def __init__(self):
        # Airport coordinates (basic set - could be expanded)
        self.airport_coords = {
            'ABE': (40.6522, -75.4402),  # Allentown
            'UKT': (40.4353, -75.3833),  # Quakertown  
            'MPO': (41.1378, -75.3789),  # Mount Pocono
            'LNS': (40.1217, -76.2961),  # Lancaster
            'PHL': (39.8719, -75.2411),  # Philadelphia
            'JFK': (40.6413, -73.7781),  # JFK
            'LAX': (33.9425, -118.4081), # LAX
            'ORD': (41.9742, -87.9073),  # Chicago
            'DFW': (32.8998, -97.0403),  # Dallas
            'ATL': (33.6407, -84.4277),  # Atlanta
            'BOS': (42.3656, -71.0096),  # Boston
            'MIA': (25.7959, -80.2870),  # Miami
            'SEA': (47.4502, -122.3088), # Seattle
            'SFO': (37.6213, -122.3790), # San Francisco
        }
        
        # Aircraft manufacturers for mission filtering
        self.manufacturers = {
            'BOEING': ['B737', 'B738', 'B739', 'B747', 'B757', 'B767', 'B777', 'B787'],
            'AIRBUS': ['A319', 'A320', 'A321', 'A330', 'A340', 'A350', 'A380'],
            'BOMBARDIER': ['CRJ2', 'CRJ7', 'CRJ9', 'DHC8', 'Q400'],
            'EMBRAER': ['E170', 'E175', 'E190', 'ERJ1'],
        }
        
        # Transpacific/Transatlantic route countries
        self.transpacific_countries = [
            'JAPAN', 'SOUTH KOREA', 'CHINA', 'HONG KONG', 'TAIWAN', 
            'PHILIPPINES', 'THAILAND', 'SINGAPORE', 'AUSTRALIA', 'NEW ZEALAND'
        ]
        
        self.transatlantic_countries = [
            'UNITED KINGDOM', 'FRANCE', 'GERMANY', 'NETHERLANDS', 'SPAIN', 
            'ITALY', 'SWITZERLAND', 'AUSTRIA', 'IRELAND', 'DENMARK', 
            'SWEDEN', 'NORWAY', 'BELGIUM', 'PORTUGAL', 'POLAND'
        ]
        
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
    
    def get_airport_coordinates(self, airport_code: str) -> Optional[Tuple[float, float]]:
        """Get airport coordinates"""
        return self.airport_coords.get(airport_code.upper())
    
    async def fetch_live_flights(self) -> List[Dict]:
        """Fetch live flight data using OpenSky Network"""
        try:
            opensky_config = os.getenv("OPENSKY_API", "{}")
            config = json.loads(opensky_config)
            
            auth = None
            if config.get("clientId") and config.get("clientSecret"):
                auth = aiohttp.BasicAuth(config["clientId"], config["clientSecret"])
            
            async with aiohttp.ClientSession(auth=auth) as session:
                url = "https://opensky-network.org/api/states/all"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        flights = []
                        if data and 'states' in data and data['states']:
                            for state in data['states']:
                                if len(state) >= 12 and state[1]:  # Has callsign
                                    # Convert from OpenSky units
                                    altitude_m = state[7] if state[7] else 0
                                    velocity_ms = state[9] if state[9] else 0
                                    
                                    flight = {
                                        'callsign': state[1].strip(),
                                        'icao24': state[0],
                                        'origin_country': state[2] or '',
                                        'longitude': state[5],
                                        'latitude': state[6], 
                                        'altitude_ft': int(altitude_m * 3.28084) if altitude_m else 0,  # Convert to feet
                                        'velocity_kts': int(velocity_ms * 1.94384) if velocity_ms else 0,  # Convert to knots
                                        'heading': state[10],
                                    }
                                    
                                    # Only include flights with valid position
                                    if flight['latitude'] and flight['longitude']:
                                        flights.append(flight)
                        
                        return flights
                    
        except Exception as e:
            print(f"Error fetching flights: {e}")
            
        return []
    
    def matches_manufacturer(self, callsign: str, manufacturer: str) -> bool:
        """Check if flight callsign suggests specific manufacturer"""
        # This is basic - in reality you'd need aircraft type data
        manufacturer = manufacturer.upper()
        if manufacturer in self.manufacturers:
            # Basic callsign pattern matching (limited without real aircraft type data)
            # This is a simplified approach
            return True  # Would need real aircraft database
        return False
    
    def matches_route_type(self, origin_country: str, route_type: str) -> bool:
        """Check if flight matches transpacific or transatlantic route"""
        country = origin_country.upper()
        
        if route_type.lower() == 'transpacific':
            return country in self.transpacific_countries
        elif route_type.lower() == 'transatlantic':
            return country in self.transatlantic_countries
            
        return False
    
    async def find_flights_by_criteria(self, airport_code: str, criteria: Dict, max_distance_km: int = 200) -> List[Dict]:
        """Find flights meeting mission criteria near specified airport"""
        coords = self.get_airport_coordinates(airport_code)
        if not coords:
            return []  # Airport not found
            
        target_lat, target_lon = coords
        flights = await self.fetch_live_flights()
        matching_flights = []
        
        for flight in flights:
            # Calculate distance from target airport
            distance = self.calculate_distance(
                target_lat, target_lon,
                flight['latitude'], flight['longitude']
            )
            
            if distance <= max_distance_km:
                # Check if flight matches criteria
                matches = True
                
                # Speed filter
                if 'min_speed' in criteria:
                    if flight['velocity_kts'] < criteria['min_speed']:
                        matches = False
                        
                if 'max_speed' in criteria:
                    if flight['velocity_kts'] > criteria['max_speed']:
                        matches = False
                
                # Altitude filter
                if 'min_altitude' in criteria:
                    if flight['altitude_ft'] < criteria['min_altitude']:
                        matches = False
                        
                if 'max_altitude' in criteria:
                    if flight['altitude_ft'] > criteria['max_altitude']:
                        matches = False
                
                # Route type filter
                if 'route_type' in criteria:
                    if not self.matches_route_type(flight['origin_country'], criteria['route_type']):
                        matches = False
                
                # Manufacturer filter (basic implementation)
                if 'manufacturer' in criteria:
                    if not self.matches_manufacturer(flight['callsign'], criteria['manufacturer']):
                        matches = False
                
                if matches:
                    flight['distance_from_target'] = round(distance, 1)
                    flight['target_airport'] = airport_code
                    matching_flights.append(flight)
        
        # Sort by distance and limit to 10 results
        matching_flights.sort(key=lambda x: x['distance_from_target'])
        return matching_flights[:10]

# Utility functions for parsing search commands
def parse_mission_command(command: str) -> Tuple[str, Dict, str]:
    """Parse mission search command"""
    # Example: "!find speed >400 ABE"
    # Example: "!find altitude >35000 PHL" 
    # Example: "!find transpacific JFK"
    
    parts = command.split()
    if len(parts) < 3:
        return "", {}, ""
        
    criteria_type = parts[1].lower()  # speed, altitude, transpacific, etc
    airport_code = parts[-1].upper()  # Last part is airport
    
    criteria = {}
    
    if criteria_type == 'speed':
        # Parse speed criteria: >400, <500, etc
        speed_part = parts[2]
        if speed_part.startswith('>'):
            criteria['min_speed'] = int(speed_part[1:])
        elif speed_part.startswith('<'):
            criteria['max_speed'] = int(speed_part[1:])
            
    elif criteria_type == 'altitude':
        # Parse altitude criteria: >35000, <40000, etc
        alt_part = parts[2]
        if alt_part.startswith('>'):
            criteria['min_altitude'] = int(alt_part[1:])
        elif alt_part.startswith('<'):
            criteria['max_altitude'] = int(alt_part[1:])
            
    elif criteria_type in ['transpacific', 'transatlantic']:
        criteria['route_type'] = criteria_type
        
    elif criteria_type == 'manufacturer':
        # !find manufacturer bombardier ABE
        if len(parts) >= 4:
            criteria['manufacturer'] = parts[2]
    
    return criteria_type, criteria, airport_code

if __name__ == "__main__":
    async def test_mission_finder():
        finder = MissionFinder()
        
        # Test speed search
        print("Testing speed >400 near ABE...")
        criteria = {'min_speed': 400}
        flights = await finder.find_flights_by_criteria('ABE', criteria)
        
        print(f"Found {len(flights)} flights >400kts near ABE:")
        for flight in flights:
            callsign = flight['callsign']
            speed = flight['velocity_kts']
            distance = flight['distance_from_target']
            print(f"  {callsign} - {speed}kts - {distance}km from ABE")
    
    asyncio.run(test_mission_finder())