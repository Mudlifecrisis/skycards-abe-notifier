#!/usr/bin/env python3
"""
User Airport Management - Multi-user airport configuration with limits
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone

class UserAirportManager:
    def __init__(self, config_file: str = "user_airports.json"):
        self.config_file = config_file
        self.max_airports_per_user = 5
        self.max_total_airports = 15
        
        # Channel mapping
        self.user_channels = {
            'gabe': 1427823232446238803,
            'mike': 1428162140564492472,
            'alex': 1428162173762404402
        }
        
        # Common airport coordinates  
        self.airport_coords = {
            'ABE': (40.6522, -75.4402),  # Allentown
            'UKT': (40.4353, -75.3833),  # Quakertown  
            'MPO': (41.1378, -75.3789),  # Mount Pocono
            'LNS': (40.1217, -76.2961),  # Lancaster
            'PHL': (39.8719, -75.2411),  # Philadelphia
            'JFK': (40.6413, -73.7781),  # JFK
            'LGA': (40.7769, -73.8740),  # LaGuardia
            'EWR': (40.6895, -74.1745),  # Newark
            'BWI': (39.1754, -76.6683),  # Baltimore
            'DCA': (38.8521, -77.0377),  # Reagan National
            'IAD': (38.9531, -77.4565),  # Dulles
            'BOS': (42.3656, -71.0096),  # Boston
            'LAX': (33.9425, -118.4081), # LAX
            'ORD': (41.9742, -87.9073),  # Chicago
            'DFW': (32.8998, -97.0403),  # Dallas
            'ATL': (33.6407, -84.4277),  # Atlanta
            'MIA': (25.7959, -80.2870),  # Miami
            'SEA': (47.4502, -122.3088), # Seattle
            'SFO': (37.6213, -122.3790), # San Francisco
            'DEN': (39.8561, -104.6737), # Denver
            'PHX': (33.4343, -112.0116), # Phoenix
            'LAS': (36.0840, -115.1537), # Las Vegas
            'MCO': (28.4312, -81.3081),  # Orlando
            'TPA': (27.9755, -82.5332),  # Tampa
        }
        
        self.user_airports = self.load_config()
        
    def load_config(self) -> Dict[str, List[str]]:
        """Load user airport configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                # Ensure all users exist with defaults
                default_config = {
                    'gabe': ['ABE', 'UKT', 'MPO', 'LNS'],  # Your current PA airports
                    'mike': [],
                    'alex': []
                }
                
                for user in default_config:
                    if user not in config:
                        config[user] = default_config[user]
                        
                return config
            except Exception as e:
                print(f"Error loading airport config: {e}")
                
        # Default configuration
        return {
            'gabe': ['ABE', 'UKT', 'MPO', 'LNS'],
            'mike': [],
            'alex': []
        }
    
    def save_config(self):
        """Save user airport configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.user_airports, f, indent=2)
        except Exception as e:
            print(f"Error saving airport config: {e}")
    
    def get_user_from_channel(self, channel_id: int) -> Optional[str]:
        """Get username from channel ID"""
        for user, ch_id in self.user_channels.items():
            if ch_id == channel_id:
                return user
        return None
    
    def get_channel_for_user(self, username: str) -> Optional[int]:
        """Get channel ID for username"""
        return self.user_channels.get(username.lower())
    
    def is_valid_airport(self, airport_code: str) -> bool:
        """Check if airport code is valid/supported"""
        return airport_code.upper() in self.airport_coords
    
    def get_user_airports(self, username: str) -> List[str]:
        """Get airports for a specific user"""
        return self.user_airports.get(username.lower(), [])
    
    def get_all_airports(self) -> Dict[str, List[str]]:
        """Get all user airports"""
        return self.user_airports.copy()
    
    def get_total_airport_count(self) -> int:
        """Get total number of airports across all users"""
        total = 0
        for airports in self.user_airports.values():
            total += len(airports)
        return total
    
    def add_airport(self, username: str, airport_code: str) -> tuple[bool, str]:
        """Add airport for user. Returns (success, message)"""
        username = username.lower()
        airport_code = airport_code.upper()
        
        # Validate airport
        if not self.is_valid_airport(airport_code):
            return False, f"❌ Airport **{airport_code}** not found in database."
        
        # Check if user exists
        if username not in self.user_airports:
            return False, f"❌ User **{username}** not found."
        
        # Check if already added
        if airport_code in self.user_airports[username]:
            return False, f"❌ You already have **{airport_code}** in your list."
        
        # Check user limit
        if len(self.user_airports[username]) >= self.max_airports_per_user:
            return False, f"❌ You already have {self.max_airports_per_user} airports (max limit)."
        
        # Check total limit
        if self.get_total_airport_count() >= self.max_total_airports:
            return False, f"❌ System limit reached ({self.max_total_airports} airports total)."
        
        # Add airport
        self.user_airports[username].append(airport_code)
        self.save_config()
        
        return True, f"✅ Added **{airport_code}** to {username}'s airport list."
    
    def remove_airport(self, username: str, airport_code: str) -> tuple[bool, str]:
        """Remove airport for user. Returns (success, message)"""
        username = username.lower()
        airport_code = airport_code.upper()
        
        # Check if user exists
        if username not in self.user_airports:
            return False, f"❌ User **{username}** not found."
        
        # Check if airport in list
        if airport_code not in self.user_airports[username]:
            return False, f"❌ **{airport_code}** not in your airport list."
        
        # Remove airport
        self.user_airports[username].remove(airport_code)
        self.save_config()
        
        return True, f"✅ Removed **{airport_code}** from {username}'s airport list."
    
    def clear_airports(self, username: str) -> tuple[bool, str]:
        """Clear all airports for user. Returns (success, message)"""
        username = username.lower()
        
        # Check if user exists
        if username not in self.user_airports:
            return False, f"❌ User **{username}** not found."
        
        count = len(self.user_airports[username])
        self.user_airports[username] = []
        self.save_config()
        
        return True, f"✅ Cleared {count} airports from {username}'s list."
    
    def get_airport_info(self, airport_code: str) -> Optional[dict]:
        """Get airport information including coordinates"""
        airport_code = airport_code.upper()
        if airport_code in self.airport_coords:
            lat, lon = self.airport_coords[airport_code]
            return {
                'code': airport_code,
                'latitude': lat,
                'longitude': lon
            }
        return None

if __name__ == "__main__":
    # Test the system
    manager = UserAirportManager()
    
    print("Current airport assignments:")
    for user, airports in manager.get_all_airports().items():
        channel = manager.get_channel_for_user(user)
        print(f"  {user}: {airports} → Channel {channel}")
    
    print(f"\nTotal airports: {manager.get_total_airport_count()}/{manager.max_total_airports}")