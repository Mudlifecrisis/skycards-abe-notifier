#!/usr/bin/env python3
"""
Summary of economic aviation APIs that include aircraft type for rare aircraft monitoring
"""

def analyze_economic_options():
    """Analyze economic options for aircraft type monitoring"""
    
    print("Economic Aviation APIs with Aircraft Type Support")
    print("=" * 60)
    print()
    
    # Economic options found
    options = [
        {
            "name": "AviationStack",
            "free_tier": "1,000 requests/month",
            "paid_tier": "$9.99/month for 10,000 requests",
            "aircraft_type_included": True,
            "aircraft_type_fields": ["aircraft.iata", "aircraft.icao", "aircraft.registration"],
            "live_data": True,
            "rare_aircraft_capable": True,
            "signup_url": "https://aviationstack.com/signup/free",
            "pros": [
                "Includes aircraft type in live flight data",
                "1000 free requests to test",
                "Low cost for paid tier",
                "REST API easy to integrate"
            ],
            "cons": [
                "Limited to 1000 requests on free tier",
                "May not cover all rare aircraft"
            ]
        },
        {
            "name": "AirLabs", 
            "free_tier": "1,000 requests/month",
            "paid_tier": "$9.99/month for 10,000 requests", 
            "aircraft_type_included": True,
            "aircraft_type_fields": ["aircraft_code", "aircraft_type"],
            "live_data": True,
            "rare_aircraft_capable": True,
            "signup_url": "https://airlabs.co/signup",
            "pros": [
                "Includes aircraft_code field for type identification",
                "1000 free requests to test",
                "Same pricing as AviationStack",
                "Good documentation"
            ],
            "cons": [
                "Limited to 1000 requests on free tier",
                "Need to verify rare aircraft coverage"
            ]
        },
        {
            "name": "OpenSky + Local Database (Hybrid)",
            "free_tier": "Unlimited (rate limited)",
            "paid_tier": "Free",
            "aircraft_type_included": False,
            "aircraft_type_fields": ["Lookup via local database"],
            "live_data": True,
            "rare_aircraft_capable": False,
            "signup_url": "None required",
            "pros": [
                "Completely free",
                "No API limits for basic usage",
                "Good for known aircraft"
            ],
            "cons": [
                "Cannot identify NEW rare aircraft",
                "Requires building local database",
                "Won't work for aircraft not in database"
            ]
        }
    ]
    
    print("RECOMMENDATION FOR RARE AIRCRAFT MONITORING:")
    print("=" * 50)
    print()
    
    print("Best approach: Start with AviationStack or AirLabs free tier")
    print()
    print("Strategy:")
    print("1. Sign up for free tier (1000 requests/month)")
    print("2. Test with known rare aircraft to verify type data")
    print("3. Build monitoring system for AB18, VUT1, etc.")
    print("4. Monitor usage - 1000 requests = ~33 checks per day")
    print("5. Upgrade to $9.99/month if needed for more frequent monitoring")
    print()
    
    for option in options:
        print(f"--- {option['name']} ---")
        print(f"Free tier: {option['free_tier']}")
        print(f"Paid tier: {option['paid_tier']}")
        print(f"Aircraft type included: {option['aircraft_type_included']}")
        if option['aircraft_type_included']:
            print(f"Type fields: {option['aircraft_type_fields']}")
        print(f"Can find rare aircraft: {option['rare_aircraft_capable']}")
        print(f"Signup: {option['signup_url']}")
        
        print("Pros:")
        for pro in option['pros']:
            print(f"  + {pro}")
        
        print("Cons:")
        for con in option['cons']:
            print(f"  - {con}")
        print()
    
    print("NEXT STEPS:")
    print("=" * 20)
    print("1. Sign up for AviationStack free account")
    print("2. Test API with a few requests to verify aircraft type data")
    print("3. Build monitoring script for your rare aircraft types")
    print("4. Set up alerts when AB18, VUT1, etc. are detected")
    print()
    print("Cost: FREE for testing, $9.99/month for serious monitoring")
    print("This is much cheaper than the $10/month ADS-B Exchange option")
    print("and actually includes the aircraft type data we need!")

if __name__ == "__main__":
    analyze_economic_options()