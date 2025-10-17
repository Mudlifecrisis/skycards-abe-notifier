#!/usr/bin/env python3
"""
Aircraft Database Manager - Downloads, stores, and manages OpenSky aircraft database locally
"""
import asyncio
import aiohttp
import csv
import json
import os
from datetime import datetime, timedelta
from io import StringIO
import pickle

class AircraftDatabaseManager:
    def __init__(self, data_dir="aircraft_data"):
        self.data_dir = data_dir
        self.db_file = os.path.join(data_dir, "aircraft_database.json")
        self.metadata_file = os.path.join(data_dir, "database_metadata.json")
        self.backup_file = os.path.join(data_dir, "aircraft_database_backup.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        self.aircraft_database = {}
        self.metadata = {}
        
    def get_database_info(self):
        """Get information about the current database"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        
        return {
            'exists': os.path.exists(self.db_file),
            'size': os.path.getsize(self.db_file) if os.path.exists(self.db_file) else 0,
            'last_updated': self.metadata.get('last_updated', 'Never'),
            'aircraft_count': self.metadata.get('aircraft_count', 0),
            'rare_aircraft_count': self.metadata.get('rare_aircraft_count', 0),
            'download_time': self.metadata.get('download_time', 0)
        }
    
    def needs_update(self, max_age_days=7):
        """Check if database needs updating"""
        info = self.get_database_info()
        
        if not info['exists']:
            return True, "Database doesn't exist"
        
        if info['last_updated'] == 'Never':
            return True, "No update timestamp"
        
        try:
            last_update = datetime.fromisoformat(info['last_updated'])
            age = datetime.now() - last_update
            
            if age > timedelta(days=max_age_days):
                return True, f"Database is {age.days} days old"
            
            return False, f"Database is current ({age.days} days old)"
            
        except Exception as e:
            return True, f"Error checking age: {e}"
    
    async def download_database(self, force=False):
        """Download OpenSky aircraft database"""
        
        print("Aircraft Database Manager")
        print("=" * 50)
        
        # Check if update is needed
        needs_update, reason = self.needs_update()
        
        if not needs_update and not force:
            print(f"Database update not needed: {reason}")
            return await self.load_local_database()
        
        print(f"Downloading database: {reason}")
        
        # Backup existing database
        if os.path.exists(self.db_file):
            print("Creating backup of existing database...")
            try:
                with open(self.db_file, 'r') as src, open(self.backup_file, 'w') as dst:
                    dst.write(src.read())
                print("Backup created successfully")
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        
        # Download from OpenSky
        db_url = "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv"
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                print("Downloading aircraft database from OpenSky...")
                async with session.get(db_url, timeout=300) as response:  # 5 minute timeout
                    if response.status == 200:
                        content = await response.text()
                        print(f"Downloaded {len(content):,} characters")
                        
                        # Parse CSV
                        print("Parsing aircraft data...")
                        csv_reader = csv.DictReader(StringIO(content))
                        
                        aircraft_db = {}
                        rare_types = {'AB18', 'VUT1', 'C17', 'F16', 'A10'}
                        rare_count = 0
                        total_count = 0
                        
                        for record in csv_reader:
                            icao24 = record.get('icao24', '').strip().lower()
                            typecode = record.get('typecode', '').strip()
                            
                            if icao24 and typecode:
                                aircraft_db[icao24] = {
                                    'type': typecode,
                                    'registration': record.get('registration', ''),
                                    'model': record.get('model', ''),
                                    'manufacturer': record.get('manufacturername', ''),
                                    'operator': record.get('operator', '')
                                }
                                total_count += 1
                                
                                if typecode in rare_types:
                                    rare_count += 1
                        
                        download_time = (datetime.now() - start_time).total_seconds()
                        
                        # Save database
                        print(f"Saving database ({total_count:,} aircraft)...")
                        with open(self.db_file, 'w') as f:
                            json.dump(aircraft_db, f, indent=2)
                        
                        # Save metadata
                        metadata = {
                            'last_updated': datetime.now().isoformat(),
                            'aircraft_count': total_count,
                            'rare_aircraft_count': rare_count,
                            'download_time': download_time,
                            'source_url': db_url,
                            'file_size': len(content)
                        }
                        
                        with open(self.metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        
                        self.aircraft_database = aircraft_db
                        self.metadata = metadata
                        
                        print(f"Database saved successfully!")
                        print(f"  Total aircraft: {total_count:,}")
                        print(f"  Rare aircraft: {rare_count}")
                        print(f"  Download time: {download_time:.1f} seconds")
                        
                        return aircraft_db
                        
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            print(f"Error downloading database: {e}")
            
            # Try to load backup
            if os.path.exists(self.backup_file):
                print("Attempting to load backup database...")
                try:
                    return await self.load_database_file(self.backup_file)
                except Exception as backup_error:
                    print(f"Backup also failed: {backup_error}")
            
            raise Exception(f"Could not download or load database: {e}")
    
    async def load_local_database(self):
        """Load database from local file"""
        return await self.load_database_file(self.db_file)
    
    async def load_database_file(self, file_path):
        """Load database from specific file"""
        
        if not os.path.exists(file_path):
            raise Exception(f"Database file not found: {file_path}")
        
        print(f"Loading database from {file_path}...")
        
        try:
            with open(file_path, 'r') as f:
                self.aircraft_database = json.load(f)
            
            print(f"Database loaded: {len(self.aircraft_database):,} aircraft")
            return self.aircraft_database
            
        except Exception as e:
            raise Exception(f"Could not load database file: {e}")
    
    def get_rare_aircraft(self, rare_types=None):
        """Get all rare aircraft from database"""
        
        if rare_types is None:
            rare_types = {'AB18', 'VUT1', 'C17', 'F16', 'A10'}
        
        rare_aircraft = {}
        
        for icao24, info in self.aircraft_database.items():
            if info['type'] in rare_types:
                rare_aircraft[icao24] = info
        
        return rare_aircraft
    
    def search_aircraft(self, search_term):
        """Search for aircraft by type, model, or registration"""
        
        search_term = search_term.upper()
        matches = []
        
        for icao24, info in self.aircraft_database.items():
            if (search_term in info['type'].upper() or 
                search_term in info['model'].upper() or
                search_term in info['registration'].upper()):
                matches.append((icao24, info))
        
        return matches

async def main():
    """Test the database manager"""
    
    manager = AircraftDatabaseManager()
    
    # Show current database info
    info = manager.get_database_info()
    print("Current Database Status:")
    print(f"  Exists: {info['exists']}")
    print(f"  Size: {info['size']:,} bytes")
    print(f"  Last updated: {info['last_updated']}")
    print(f"  Aircraft count: {info['aircraft_count']:,}")
    print(f"  Rare aircraft: {info['rare_aircraft_count']}")
    print()
    
    # Load or download database
    try:
        aircraft_db = await manager.download_database()
        
        # Show rare aircraft
        rare_aircraft = manager.get_rare_aircraft()
        print(f"\nRare Aircraft Found ({len(rare_aircraft)}):")
        
        rare_by_type = {}
        for icao24, info in rare_aircraft.items():
            aircraft_type = info['type']
            if aircraft_type not in rare_by_type:
                rare_by_type[aircraft_type] = []
            rare_by_type[aircraft_type].append((icao24, info))
        
        for aircraft_type, aircraft_list in rare_by_type.items():
            print(f"  {aircraft_type}: {len(aircraft_list)} aircraft")
            for icao24, info in aircraft_list[:3]:  # Show first 3
                print(f"    {icao24}: {info['registration']} - {info['model']}")
        
        print(f"\nDatabase ready for monitoring!")
        
    except Exception as e:
        print(f"Failed to load database: {e}")

if __name__ == "__main__":
    asyncio.run(main())