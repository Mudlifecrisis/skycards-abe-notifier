# API Usage Optimization - Multi-User Configuration

## Final Configuration (Optimized for OpenSky API Limits)

### Limits
- **Max airports per user**: 3 
- **Max total airports**: 9 (3 users × 3 airports)
- **Check interval**: 5 minutes (300 seconds)
- **Active hours**: 6am-midnight (18 hours)
- **Quiet hours**: midnight-6am (6 hours)

### API Usage Calculation
```
Daily calls = 3 users × 3 airports × 12 calls/hour × 18 hours
Daily calls = 1,944 calls/day
OpenSky limit = 4,000 calls/day
Buffer = 2,056 calls/day (51% buffer)
```

### Benefits of This Configuration
1. **Extended coverage**: 18 hours of monitoring (6am-midnight)
2. **Multiple airports**: Each user can monitor 3 different airports
3. **Safety buffer**: Only uses 49% of daily API limit
4. **Manual search capacity**: Plenty of API calls left for manual searches
5. **Real-time alerts**: 5-minute intervals still catch aircraft effectively

### Comparison vs Previous Ideas

#### Option A: 2 minutes, 2 airports, 6am-11pm
- Daily calls: 3 × 2 × 30 × 17 = 3,060 calls/day
- Buffer: 940 calls (23% buffer)
- Risk: Less headroom for manual searches

#### Option B: 5 minutes, 5 airports, 6am-11pm  
- Daily calls: 3 × 5 × 12 × 17 = 3,060 calls/day
- Buffer: 940 calls (23% buffer)
- Risk: Hitting user limit per airport too quickly

#### **Selected Option C: 5 minutes, 3 airports, 6am-midnight**
- Daily calls: 3 × 3 × 12 × 18 = 1,944 calls/day
- Buffer: 2,056 calls (51% buffer)
- Benefits: Best balance of coverage, safety, and extended hours

### Implementation Changes
- `user_airports.py`: Reduced limits from 5→3 airports per user
- `bot.py`: Changed interval from 120→300 seconds (2min→5min)
- `.env`: Set QUIET_START=0, QUIET_END=6 (midnight-6am quiet)
- Default user config: Reduced from 4→3 airports for existing users

### Future Expansion
If we get more users or want higher frequency:
1. **OpenSky Premium**: $10/month for 10,000 calls/day
2. **Hybrid approach**: Core airports on 5-min, priority on 2-min
3. **Smart scheduling**: Higher frequency during peak hours
4. **Landing-only mode**: Use `/flights/arrival` for specific destination monitoring