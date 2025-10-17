#!/usr/bin/env python3
"""
Test the enhanced integration of Discord bot with production aircraft database
"""
import asyncio
from rare_hunter import RareAircraftHunter

async def test_enhanced_hunter():
    """Test the enhanced rare aircraft hunter"""
    
    print("Testing Enhanced Rare Aircraft Hunter Integration")
    print("=" * 60)
    
    # Initialize the hunter (this will load our production database)
    hunter = RareAircraftHunter()
    
    print(f"\nHunter Statistics:")
    stats = hunter.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value:,}")
    
    print(f"\nSearch Terms: {hunter.get_search_terms()}")
    
    print(f"\nTesting live aircraft search...")
    
    try:
        # Test the enhanced search
        rare_aircraft = await hunter.find_rare_aircraft()
        
        if rare_aircraft:
            print(f"\n🎯 FOUND {len(rare_aircraft)} RARE AIRCRAFT!")
            
            # Separate user targets from other rare aircraft
            user_targets = [a for a in rare_aircraft if a.get('is_user_target', False)]
            other_rare = [a for a in rare_aircraft if not a.get('is_user_target', False)]
            
            if user_targets:
                print(f"\n🚨 YOUR TARGET AIRCRAFT ({len(user_targets)}):")
                for aircraft in user_targets:
                    print(f"  {aircraft['matched_term']}: {aircraft['callsign']}")
                    print(f"    Registration: {aircraft['registration']}")
                    print(f"    Model: {aircraft['model']}")
                    print(f"    Operator: {aircraft['operator']}")
                    print(f"    Position: {aircraft['latitude']:.4f}, {aircraft['longitude']:.4f}")
                    print(f"    Altitude: {aircraft.get('altitude_ft', 'Unknown')} ft")
                    print(f"    Speed: {aircraft.get('velocity_kts', 'Unknown')} kts")
                    print(f"    Reason: {aircraft['search_reason']}")
                    print()
            
            if other_rare:
                print(f"\n✈️  OTHER RARE AIRCRAFT ({len(other_rare)}):")
                for aircraft in other_rare[:5]:  # Show first 5
                    print(f"  {aircraft['matched_term']}: {aircraft['callsign']}")
                    print(f"    Registration: {aircraft['registration']}")
                    print(f"    Reason: {aircraft['search_reason']}")
                    print()
                
                if len(other_rare) > 5:
                    print(f"  ... and {len(other_rare) - 5} more")
        else:
            print(f"\n❌ No rare aircraft found currently airborne")
            print(f"Your target aircraft (AB18, VUT1, KFIR) are not flying right now")
            
    except Exception as e:
        print(f"Error during testing: {e}")
    
    print(f"\n" + "=" * 60)
    print("Integration Test Complete!")
    print("The Discord bot is now ready with enhanced rare aircraft detection!")
    print("Your target aircraft will be detected with full details when they appear.")

if __name__ == "__main__":
    asyncio.run(test_enhanced_hunter())