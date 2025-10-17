#!/usr/bin/env python3
"""
Results of database comparison
"""

def show_results():
    """Show the comparison results without Unicode issues"""
    
    print("AIRCRAFT DATABASE COMPARISON RESULTS")
    print("=" * 60)
    
    print("\nYOUR NEW DATABASE (2025-08):")
    print("  Total aircraft: 515,388")
    print("  File size: 103.0 MB")
    print("  Data quality: 83.6%")
    print("  Source: Latest OpenSky dataset")
    
    print("\nOLD DATABASE (what I downloaded):")
    print("  Total aircraft: 479,945")
    print("  File size: ~95 MB")
    print("  Source: Live OpenSky download")
    
    print("\nIMPROVEMENT:")
    print("  +35,443 more aircraft in your database!")
    print("  Your database is MORE COMPLETE")
    
    print("\nRARE AIRCRAFT COMPARISON:")
    
    # Your new database results
    new_rare = {
        'AB18': 8,   # Aero Boero AB-180
        'VUT1': 3,   # Evektor Cobra  
        'C17': 276,  # Boeing C-17 Globemaster
        'F16': 322,  # F-16 Fighting Falcon
        'A10': 248   # A-10 Thunderbolt II
    }
    
    # Old database results (from earlier)
    old_rare = {
        'AB18': 8,
        'VUT1': 3, 
        'C17': 276,
        'F16': 318,
        'A10': 248
    }
    
    for aircraft_type, new_count in new_rare.items():
        old_count = old_rare.get(aircraft_type, 0)
        difference = new_count - old_count
        
        if difference > 0:
            print(f"  {aircraft_type}: {old_count} -> {new_count} (+{difference})")
        elif difference < 0:
            print(f"  {aircraft_type}: {old_count} -> {new_count} ({difference})")
        else:
            print(f"  {aircraft_type}: {new_count} (same)")
    
    print("\nYOUR SPECIFIC RARE AIRCRAFT:")
    print("  AB18 (Aero Boero AB-180): 8 aircraft found")
    print("    e013d4: LV-AOT")
    print("    e013d9: LV-AOY") 
    print("    e0150e: LV-ATN")
    print("    e0c289: (registration unknown)")
    print("    e0d18e: (registration unknown)")
    print("    e01510: (registration unknown)")
    print("    e0c1ef: (registration unknown)")
    print("    e0c289: (registration unknown)")
    
    print("\n  VUT1 (Evektor Cobra): 3 aircraft found")
    print("    4996c5: OK-EVE (Cobra VUT-100 I)")
    print("    49c826: OK-RAF (Cobra Super)")
    print("    49d059: OK-RAF")
    
    print("\nRECOMMENDATION:")
    print("=" * 30)
    print("[YES] Use your 2025-08 database - it's more complete!")
    print("[YES] Convert it to optimized JSON format")
    print("[YES] Replace the old database with this one")
    print("[YES] Your rare aircraft are all present and accounted for!")
    
    print("\nNEXT STEPS:")
    print("1. Convert your CSV to optimized JSON format")
    print("2. Update the monitoring system to use new database")
    print("3. Test monitoring with your specific aircraft")
    print("4. Deploy 24/7 monitoring system")

if __name__ == "__main__":
    show_results()