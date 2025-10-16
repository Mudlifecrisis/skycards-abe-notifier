#!/usr/bin/env python3
"""
Alert Acknowledgment System - Track and remind about unacknowledged aircraft alerts
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class AlertTracker:
    def __init__(self, alerts_file: str = "pending_alerts.json"):
        self.alerts_file = alerts_file
        self.reminder_delay_minutes = 30
        self.pending_alerts = self.load_alerts()
    
    def load_alerts(self) -> Dict[str, dict]:
        """Load pending alerts from file"""
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading alerts: {e}")
        return {}
    
    def save_alerts(self):
        """Save pending alerts to file"""
        try:
            with open(self.alerts_file, 'w') as f:
                json.dump(self.pending_alerts, f, indent=2)
        except Exception as e:
            print(f"Error saving alerts: {e}")
    
    def add_alert(self, alert_id: str, aircraft_data: dict, channel_id: int, user: str = None):
        """Add new alert to tracking system"""
        now = datetime.utcnow()
        alert_info = {
            'aircraft_data': aircraft_data,
            'channel_id': channel_id,
            'user': user,
            'created_at': now.isoformat(),
            'reminder_at': (now + timedelta(minutes=self.reminder_delay_minutes)).isoformat(),
            'reminded': False,
            'acknowledged': False
        }
        
        self.pending_alerts[alert_id] = alert_info
        self.save_alerts()
        
        print(f"Added alert tracking for {aircraft_data.get('callsign', 'Unknown')} - reminder in {self.reminder_delay_minutes}min")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        if alert_id in self.pending_alerts:
            self.pending_alerts[alert_id]['acknowledged'] = True
            self.save_alerts()
            return True
        return False
    
    def get_alerts_needing_reminder(self) -> List[tuple]:
        """Get alerts that need reminder (past reminder time, not reminded, not acknowledged)"""
        now = datetime.utcnow()
        reminders_needed = []
        
        for alert_id, alert_info in self.pending_alerts.items():
            if alert_info['acknowledged'] or alert_info['reminded']:
                continue
                
            reminder_time = datetime.fromisoformat(alert_info['reminder_at'])
            if now >= reminder_time:
                reminders_needed.append((alert_id, alert_info))
        
        return reminders_needed
    
    def mark_reminded(self, alert_id: str):
        """Mark alert as reminded"""
        if alert_id in self.pending_alerts:
            self.pending_alerts[alert_id]['reminded'] = True
            self.save_alerts()
    
    def cleanup_old_alerts(self, max_age_hours: int = 6):
        """Remove alerts older than max_age_hours"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=max_age_hours)
        
        alerts_to_remove = []
        for alert_id, alert_info in self.pending_alerts.items():
            created_time = datetime.fromisoformat(alert_info['created_at'])
            if created_time < cutoff:
                alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.pending_alerts[alert_id]
        
        if alerts_to_remove:
            self.save_alerts()
            print(f"Cleaned up {len(alerts_to_remove)} old alerts")
    
    def get_alert_status(self) -> dict:
        """Get summary of alert status"""
        total = len(self.pending_alerts)
        acknowledged = sum(1 for a in self.pending_alerts.values() if a['acknowledged'])
        reminded = sum(1 for a in self.pending_alerts.values() if a['reminded'])
        pending = total - acknowledged
        
        return {
            'total': total,
            'acknowledged': acknowledged,
            'reminded': reminded,
            'pending': pending
        }
    
    def create_alert_id(self, aircraft_data: dict) -> str:
        """Create unique alert ID from aircraft data"""
        icao24 = aircraft_data.get('icao24', 'unknown')
        callsign = aircraft_data.get('callsign', 'unknown').strip()
        timestamp = datetime.utcnow().strftime('%H%M')
        return f"{icao24}_{callsign}_{timestamp}"
    
    def create_reminder_embed(self, alert_id: str, alert_info: dict) -> dict:
        """Create Discord embed for reminder"""
        aircraft_data = alert_info['aircraft_data']
        callsign = aircraft_data.get('callsign', 'Unknown').strip()
        icao24 = aircraft_data.get('icao24', 'Unknown')
        
        # Calculate how long ago the original alert was
        created_time = datetime.fromisoformat(alert_info['created_at'])
        time_ago = datetime.utcnow() - created_time
        minutes_ago = int(time_ago.total_seconds() / 60)
        
        embed = {
            'title': f"REMINDER: {callsign}",
            'description': f"This alert was sent **{minutes_ago} minutes ago** and hasn't been acknowledged.",
            'color': 0xFFA500,  # Orange
            'fields': [
                {
                    'name': 'Aircraft',
                    'value': f"**{callsign}** ({icao24})",
                    'inline': True
                },
                {
                    'name': 'Original Alert',
                    'value': f"{minutes_ago} minutes ago",
                    'inline': True
                },
                {
                    'name': 'User',
                    'value': alert_info.get('user', 'System'),
                    'inline': True
                }
            ],
            'footer': {
                'text': f"React with checkmark to acknowledge • Alert ID: {alert_id[:8]}"
            }
        }
        
        return embed

if __name__ == "__main__":
    # Test the alert tracker
    tracker = AlertTracker()
    
    # Example aircraft data
    test_aircraft = {
        'icao24': 'abc123',
        'callsign': 'BADGR33',
        'altitude': 35000,
        'velocity': 450
    }
    
    # Add test alert
    alert_id = tracker.create_alert_id(test_aircraft)
    tracker.add_alert(alert_id, test_aircraft, 123456789, 'gabe')
    
    print("Alert status:", tracker.get_alert_status())
    print("Alerts needing reminder:", len(tracker.get_alerts_needing_reminder()))