#!/usr/bin/env python3
"""
Test Alert Acknowledgment System
"""
from alert_tracker import AlertTracker
from datetime import datetime, timedelta

def test_alert_system():
    """Test the alert tracking and reminder system"""
    print("Testing Alert Acknowledgment System\n")
    
    # Create tracker
    tracker = AlertTracker("test_alerts.json")
    
    # Test aircraft data
    test_aircraft = {
        'icao24': 'abc123',
        'callsign': 'BADGR33',
        'registration': 'N123AB',
        'aircraft_type': 'KC135',
        'airline': 'US Air Force',
        'departure': 'JFK',
        'arrival': 'ABE',
        'eta': '2024-01-01T15:30:00Z',
        'rarity': 6.5,
        'tag': '🟣 RARE'
    }
    
    # Add test alert
    alert_id = tracker.create_alert_id(test_aircraft)
    tracker.add_alert(alert_id, test_aircraft, 123456789, 'gabe')
    
    print(f"Added test alert: {alert_id}")
    print("Alert status:", tracker.get_alert_status())
    
    # Test immediate reminder check (should be empty)
    reminders_needed = tracker.get_alerts_needing_reminder()
    print(f"Reminders needed now: {len(reminders_needed)}")
    
    # Simulate time passing by manually setting reminder time to past
    if alert_id in tracker.pending_alerts:
        past_time = datetime.utcnow() - timedelta(minutes=1)
        tracker.pending_alerts[alert_id]['reminder_at'] = past_time.isoformat()
        tracker.save_alerts()
        
        # Check again
        reminders_needed = tracker.get_alerts_needing_reminder()
        print(f"Reminders needed after time simulation: {len(reminders_needed)}")
        
        if reminders_needed:
            alert_id, alert_info = reminders_needed[0]
            embed_data = tracker.create_reminder_embed(alert_id, alert_info)
            print("\nReminder embed:")
            print(f"Title: {embed_data['title']}")
            print(f"Description: {embed_data['description']}")
            print(f"Color: {hex(embed_data['color'])}")
            
            # Test acknowledgment
            tracker.acknowledge_alert(alert_id)
            print(f"\nAlert {alert_id[:8]} acknowledged")
            
    print("\nFinal status:", tracker.get_alert_status())
    
    # Cleanup
    import os
    if os.path.exists("test_alerts.json"):
        os.remove("test_alerts.json")
    print("\nTest file cleaned up")

if __name__ == "__main__":
    test_alert_system()