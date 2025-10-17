#!/usr/bin/env python3
"""
Test OpenSky database with actual rare aircraft from user's Skycards catches
"""
import asyncio
import aiohttp
import json

async def test_rare_aircraft_examples():
    """Test specific rare aircraft types from user's actual catches"""
    
    print("Testing OpenSky Database with Real Rare Aircraft Catches")
    print("="*70)
    
    # Aircraft we're looking for (from user's catches)
    target_aircraft = {
        "Aero Boero AB-180": ["AB18"],
        "Evektor Cobra": ["VUT1"], 
        "Travel Air 5": ["AA5", "TVL4", "TVLB"],  # Multiple possible codes
        "Boeing C-135 Stratolifter": ["C135"]
    }
    
    print("Step 1: Getting live aircraft to find examples...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get all live aircraft
            async with session.get("https://opensky-network.org/api/states/all") as response:
                if response.status == 200:
                    data = await response.json()
                    states = data.get('states', [])
                    
                    print(f"Found {len(states)} live aircraft")
                    
                    # Test a sample to look for our target aircraft types
                    print("\nStep 2: Testing sample aircraft in database...")
                    
                    found_examples = {}
                    tested_count = 0
                    
                    for state in states[:100]:  # Test first 100 aircraft
                        icao24 = state[0]
                        callsign = (state[1] or "").strip()
                        
                        tested_count += 1
                        
                        try:
                            # Check OpenSky aircraft database
                            url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
                            async with session.get(url) as db_response:
                                if db_response.status == 200:
                                    aircraft_data = await db_response.json()
                                    
                                    aircraft_type = aircraft_data.get('typecode', '')
                                    model = aircraft_data.get('model', '')
                                    manufacturer = aircraft_data.get('manufacturerName', '')
                                    
                                    # Check if this matches any of our target aircraft
                                    for target_name, target_codes in target_aircraft.items():
                                        if aircraft_type in target_codes:
                                            if target_name not in found_examples:
                                                found_examples[target_name] = []
                                            
                                            found_examples[target_name].append({
                                                'icao24': icao24,
                                                'callsign': callsign,
                                                'typecode': aircraft_type,
                                                'model': model,
                                                'manufacturer': manufacturer
                                            })
                                            
                                            print(f"  FOUND: {target_name} → {callsign} ({icao24}) = {aircraft_type}")
                        
                        except Exception as e:
                            pass  # Skip errors, just testing coverage
                            
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                        # Stop if we found all types
                        if len(found_examples) >= len(target_aircraft):
                            break
                    
                    print(f"\nStep 3: Results after testing {tested_count} aircraft")
                    print("="*70)
                    
                    for target_name, target_codes in target_aircraft.items():
                        if target_name in found_examples:
                            examples = found_examples[target_name]
                            print(f"\n✅ {target_name}")
                            print(f"   Target codes: {target_codes}")
                            for example in examples[:3]:  # Show up to 3 examples
                                print(f"   Found: {example['callsign']} ({example['icao24']}) → {example['typecode']}")
                                print(f"          {example['manufacturer']} {example['model']}")
                        else:
                            print(f"\n❓ {target_name}")
                            print(f"   Target codes: {target_codes}")
                            print("   No live examples found (but could still work with the right ICAO24)")
                    
                    print("\n" + "="*70)
                    print("ANALYSIS:")
                    print(f"- Tested {tested_count} aircraft")
                    print(f"- Found {len(found_examples)} out of {len(target_aircraft)} target aircraft types")
                    print("- This shows OpenSky database coverage for rare aircraft types")
                    
    except Exception as e:
        print(f"Error testing aircraft: {e}")

if __name__ == "__main__":
    asyncio.run(test_rare_aircraft_examples())