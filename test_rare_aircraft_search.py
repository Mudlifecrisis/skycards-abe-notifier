#!/usr/bin/env python3
"""
Search plane-alert-db for the user's rare aircraft
"""
import asyncio
import aiohttp
import csv
from io import StringIO

async def search_rare_aircraft():
    """Search for user's specific rare aircraft in plane-alert-db"""
    
    print("Searching plane-alert-db for Your Rare Aircraft")
    print("=" * 60)
    
    # Your rare aircraft to search for
    rare_aircraft = [
        "Aero Boero AB-180",
        "Evektor Cobra", 
        "Travel Air 5",
        "Boeing C-135 STRATOLIFTER"
    ]
    
    # Search terms and variations to look for
    search_terms = {
        "Aero Boero AB-180": ["aero", "boero", "ab-180", "ab180", "ab18"],
        "Evektor Cobra": ["evektor", "cobra", "vut1"],
        "Travel Air 5": ["travel", "air", "ta5", "travelair"],
        "Boeing C-135 STRATOLIFTER": ["c-135", "c135", "stratolifter", "kc135", "kc-135"]
    }
    
    csv_url = "https://raw.githubusercontent.com/sdr-enthusiasts/plane-alert-db/main/plane-alert-db.csv"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(csv_url) as response:
                if response.status == 200:
                    content = await response.text()
                    csv_reader = csv.DictReader(StringIO(content))
                    records = list(csv_reader)
                    
                    print(f"Searching {len(records)} aircraft records...")
                    
                    # Search for each rare aircraft
                    for aircraft_name in rare_aircraft:
                        print(f"\n--- Searching for: {aircraft_name} ---")
                        
                        found_matches = []
                        search_words = search_terms[aircraft_name]
                        
                        for record in records:
                            icao24 = record.get('$ICAO', '').lower()
                            aircraft_type = record.get('$Type', '').lower()
                            icao_type = record.get('$ICAO Type', '').upper()
                            operator = record.get('$Operator', '')
                            
                            # Check if any search terms match
                            text_to_search = f"{aircraft_type} {icao_type}".lower()
                            
                            for search_word in search_words:
                                if search_word.lower() in text_to_search:
                                    found_matches.append({
                                        'icao24': icao24,
                                        'type': record.get('$Type', ''),
                                        'icao_type': icao_type,
                                        'operator': operator,
                                        'matched_term': search_word
                                    })
                                    break
                        
                        if found_matches:
                            print(f"[FOUND] {len(found_matches)} matches:")
                            for match in found_matches[:10]:  # Show first 10
                                print(f"  {match['icao24']}: {match['type']} ({match['icao_type']}) - {match['operator']}")
                                print(f"    Matched: '{match['matched_term']}'")
                        else:
                            print("[NOT FOUND] No matches in database")
                    
                    # Also do a broader search for any uncommon aircraft types
                    print(f"\n--- Looking for Rare/Uncommon Aircraft Types ---")
                    
                    # Count aircraft by type to find rare ones
                    type_counts = {}
                    for record in records:
                        icao_type = record.get('$ICAO Type', '').upper()
                        if icao_type:
                            type_counts[icao_type] = type_counts.get(icao_type, 0) + 1
                    
                    # Find aircraft types with very few instances (rare)
                    rare_types = [(t, count) for t, count in type_counts.items() if count <= 5]
                    rare_types.sort(key=lambda x: x[1])
                    
                    print(f"\nRarest aircraft types in database (5 or fewer):")
                    for aircraft_type, count in rare_types[:20]:  # Show 20 rarest
                        print(f"  {aircraft_type}: {count} aircraft")
                        
                        # Show examples of this rare type
                        examples = []
                        for record in records:
                            if record.get('$ICAO Type', '').upper() == aircraft_type:
                                examples.append(record.get('$Type', ''))
                                if len(examples) >= 2:  # Show up to 2 examples
                                    break
                        
                        if examples:
                            print(f"    Examples: {', '.join(examples)}")
                    
    except Exception as e:
        print(f"Error searching rare aircraft: {e}")

if __name__ == "__main__":
    asyncio.run(search_rare_aircraft())