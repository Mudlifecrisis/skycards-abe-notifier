#!/usr/bin/env python3
"""
Search for IAI Kfir aircraft in the database
"""
import json

def search_kfir():
    """Search for IAI Kfir aircraft"""
    
    print("Searching for IAI Kfir Aircraft")
    print("=" * 50)
    
    try:
        # Load the production database
        with open("aircraft_data/production_aircraft_database.json", 'r') as f:
            db_data = json.load(f)
        
        aircraft_db = db_data['aircraft']
        
        print(f"Searching {len(aircraft_db):,} aircraft...")
        
        # Search for Kfir aircraft
        kfir_aircraft = []
        search_terms = ['KFIR', 'C2', 'C7', 'IAI']
        
        for icao24, info in aircraft_db.items():
            aircraft_type = info.get('type', '').upper()
            model = info.get('model', '').upper()
            manufacturer = info.get('manufacturername', '').upper()
            
            # Search in type, model, and manufacturer fields
            search_text = f"{aircraft_type} {model} {manufacturer}"
            
            # Check for Kfir-related terms
            if any(term in search_text for term in search_terms):
                # Additional check for actual Kfir mentions
                if 'KFIR' in search_text or ('IAI' in search_text and ('C2' in search_text or 'C7' in search_text)):
                    kfir_aircraft.append((icao24, info))
        
        print(f"\nSearch Results:")
        if kfir_aircraft:
            print(f"Found {len(kfir_aircraft)} potential Kfir aircraft:")
            
            for icao24, info in kfir_aircraft:
                print(f"\n  ICAO24: {icao24}")
                print(f"  Type: {info.get('type', 'Unknown')}")
                print(f"  Registration: {info.get('registration', 'Unknown')}")
                print(f"  Model: {info.get('model', 'Unknown')}")
                print(f"  Manufacturer: {info.get('manufacturer', 'Unknown')}")
                print(f"  Operator: {info.get('operator', 'Unknown')}")
        else:
            print("No Kfir aircraft found in database")
            
            # Try broader search for IAI aircraft
            print(f"\nTrying broader search for IAI aircraft...")
            iai_aircraft = []
            
            for icao24, info in aircraft_db.items():
                manufacturer = info.get('manufacturer', '').upper()
                model = info.get('model', '').upper()
                
                if 'IAI' in manufacturer or 'ISRAEL' in manufacturer:
                    iai_aircraft.append((icao24, info))
            
            if iai_aircraft:
                print(f"Found {len(iai_aircraft)} IAI aircraft:")
                for icao24, info in iai_aircraft[:10]:  # Show first 10
                    print(f"  {icao24}: {info.get('type', '')} - {info.get('model', '')} ({info.get('registration', '')})")
                if len(iai_aircraft) > 10:
                    print(f"  ... and {len(iai_aircraft) - 10} more")
            else:
                print("No IAI aircraft found")
        
        # Check current live aircraft
        print(f"\nChecking live aircraft for Kfir...")
        return search_live_kfir(kfir_aircraft)
        
    except Exception as e:
        print(f"Error searching for Kfir: {e}")
        return []

def search_live_kfir(kfir_aircraft):
    """Check if any Kfir aircraft are currently in the air"""
    
    if not kfir_aircraft:
        print("No Kfir aircraft in database to check")
        return []
    
    import asyncio
    import aiohttp
    
    async def check_live():
        kfir_icao24s = [icao24 for icao24, info in kfir_aircraft]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://opensky-network.org/api/states/all", timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        states = data.get('states', [])
                        
                        print(f"Checking {len(states)} live aircraft...")
                        
                        live_kfir = []
                        
                        for state in states:
                            if not state or len(state) < 1:
                                continue
                            
                            icao24 = state[0].strip().lower() if state[0] else ''
                            
                            if icao24 in kfir_icao24s:
                                # Found a live Kfir!
                                callsign = state[1].strip() if state[1] else 'Unknown'
                                lat = state[6] if state[6] else 'Unknown'
                                lon = state[5] if state[5] else 'Unknown'
                                altitude = state[7] if state[7] else 'Unknown'
                                
                                # Get aircraft info
                                aircraft_info = next(info for icao, info in kfir_aircraft if icao == icao24)
                                
                                live_kfir.append({
                                    'icao24': icao24,
                                    'callsign': callsign,
                                    'position': f"{lat}, {lon}",
                                    'altitude': f"{altitude} ft" if altitude != 'Unknown' else 'Unknown',
                                    'info': aircraft_info
                                })
                        
                        if live_kfir:
                            print(f"\n*** KFIR AIRCRAFT CURRENTLY IN THE AIR! ***")
                            print("=" * 60)
                            
                            for aircraft in live_kfir:
                                print(f"ICAO24: {aircraft['icao24']}")
                                print(f"Type: {aircraft['info'].get('type', 'Unknown')}")
                                print(f"Registration: {aircraft['info'].get('registration', 'Unknown')}")
                                print(f"Model: {aircraft['info'].get('model', 'Unknown')}")
                                print(f"Operator: {aircraft['info'].get('operator', 'Unknown')}")
                                print(f"Callsign: {aircraft['callsign']}")
                                print(f"Position: {aircraft['position']}")
                                print(f"Altitude: {aircraft['altitude']}")
                                print("-" * 40)
                        else:
                            print("No Kfir aircraft currently airborne")
                        
                        return live_kfir
                        
                    else:
                        print(f"Error checking live aircraft: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error checking live aircraft: {e}")
            return []
    
    return asyncio.run(check_live())

def add_kfir_to_monitoring(kfir_aircraft):
    """Add Kfir aircraft to monitoring configuration"""
    
    if not kfir_aircraft:
        print("No Kfir aircraft to add to monitoring")
        return
    
    try:
        # Load current config
        with open("aircraft_data/monitoring_config.json", 'r') as f:
            config = json.load(f)
        
        # Add Kfir to target aircraft
        # First, find the ICAO type code for Kfir
        kfir_type = None
        for icao24, info in kfir_aircraft:
            kfir_type = info.get('type', '')
            if kfir_type:
                break
        
        if kfir_type:
            config['target_aircraft'][kfir_type] = {
                'name': 'IAI Kfir',
                'priority': 'HIGH',
                'notify': True,
                'sound_alert': True
            }
            
            # Save updated config
            with open("aircraft_data/monitoring_config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"\nKfir aircraft ({kfir_type}) added to monitoring configuration!")
            print(f"The monitoring system will now alert for Kfir aircraft.")
        else:
            print("Could not determine Kfir type code for monitoring")
            
    except Exception as e:
        print(f"Error updating monitoring config: {e}")

def main():
    """Main search function"""
    
    kfir_aircraft = search_kfir()
    
    if kfir_aircraft:
        live_kfir = search_live_kfir(kfir_aircraft)
        
        # Add to monitoring if found
        add_kfir_to_monitoring(kfir_aircraft)
        
        print(f"\n" + "=" * 60)
        print("KFIR SEARCH COMPLETE")
        print("=" * 60)
        print(f"Kfir aircraft in database: {len(kfir_aircraft)}")
        print(f"Kfir aircraft currently airborne: {len(live_kfir) if isinstance(live_kfir, list) else 0}")
        
        if kfir_aircraft:
            print(f"Kfir aircraft added to monitoring system!")
            print(f"Start the monitor to watch for them: python start_monitor.py")

if __name__ == "__main__":
    main()