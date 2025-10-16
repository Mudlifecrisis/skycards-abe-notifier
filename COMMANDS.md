# Skycards Bot Commands Reference

## 🆘 Help
- `!` - Show complete command help menu

## 🔍 Mission Search
Find flights meeting specific criteria near airports:
- `!find speed >400 ABE` - Find flights traveling >400kts near ABE
- `!find altitude >35000 PHL` - Find flights above 35,000ft near PHL  
- `!find manufacturer boeing JFK` - Find Boeing aircraft near JFK
- `!find route transpacific LAX` - Find transpacific routes near LAX

**Format:** `!find [criteria] [airport_code]`
- Searches within 200km radius
- Returns max 10 results per search
- Supports: speed, altitude, manufacturer, route type

## ✈️ Rare Aircraft Hunting
Global search for military and rare civilian aircraft:
- `!add chinook` - Add search term (gets AI suggestions)
- `!list` - Show current search terms
- `!stats` - Show hunting statistics  
- `!hunt` - Force search now (manual trigger)
- `!alerts` - Show alert acknowledgment status

**Search Terms Examples:**
- Military callsigns: `BADGR33`, `RCH`, `QID`
- Aircraft types: `KC135`, `C17`, `B35`
- Generic terms: `chinook`, `stratotanker`

## 🏢 Airport Management
Multi-user airport monitoring (max 3 airports per user):
- `!airports list` - Show your monitored airports
- `!airports add PHL` - Add airport to your monitoring list
- `!airports remove LAX` - Remove airport from list
- `!airports clear` - Clear all your airports

**Monitoring Details:**
- 5-minute check intervals
- Active hours: 6am-midnight
- Quiet hours: midnight-6am
- Individual Discord channels per user

## 🤖 Airport Assistant
AI-powered airport discovery using natural language:
- `!airports_llm find dubai airport` - Ask about specific airports
- `!airports_llm best cargo hub europe` - Ask for recommendations
- `!airports_llm airport near london international` - Location queries

**Powered by DeepSeek AI** - understands complex airport queries

## ⚙️ System & Alerts
- `!` - Show help menu
- React with ✅ to acknowledge aircraft alerts
- **Auto-reminders**: Unacknowledged alerts get reminded after 30 minutes
- **Alert tracking**: Each alert gets unique ID in footer

## 💡 Usage Tips

### Alert Acknowledgment
1. Aircraft alert appears with ✅ reaction
2. Click ✅ to acknowledge you've seen it
3. If not acknowledged in 30 minutes → reminder sent
4. Reminders also get ✅ reactions for acknowledgment

### Multi-User Setup
- Each user gets their own airport monitoring channel
- Configure your own airports independently  
- System handles 3 users × 3 airports = 9 total max
- API usage optimized to stay under OpenSky limits

### Mission Search Examples
```
!find speed >450 JFK          # Fast flights near JFK
!find altitude >40000 LAX      # High-altitude flights  
!find manufacturer airbus DFW  # Airbus aircraft
!find route transatlantic BOS  # Transatlantic routes
```

### Best Practices
- Acknowledge alerts promptly to avoid reminders
- Use specific search terms for better rare aircraft detection
- Monitor airports relevant to your interests/location
- Use airport assistant for discovering new airports to monitor

## 🔧 Technical Details
- **API Limits**: Optimized for OpenSky Network free tier (4,000 calls/day)
- **Monitoring Frequency**: 5 minutes for airport alerts, 3 minutes for rare hunting
- **Search Range**: 200km radius for mission search, global for rare hunting
- **Data Sources**: OpenSky Network + DeepSeek AI + AeroDataBox (future)