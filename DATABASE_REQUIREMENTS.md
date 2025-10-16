# Aircraft Database Requirements Analysis

*Session Date: October 16, 2025*

## 🎯 **The Missing Piece**

Our system can get live aircraft positions but **cannot identify aircraft types**. This is the core blocker for proper search functionality.

## 📊 **What We Have vs What We Need**

### **Current Data (OpenSky API)**
```json
{
  "icao24": "ae117c",        // ✅ Unique aircraft identifier
  "callsign": "RCH4231",     // ✅ Current flight callsign  
  "origin_country": "United States",
  "latitude": 38.782,
  "longitude": -75.663,
  "altitude": 11400,
  "velocity": 345
}
```

### **Missing Data (Aircraft Type Information)**
```json
{
  "icao24": "ae117c",
  // MISSING:
  "icao_type": "C17",                    // ICAO aircraft type designator
  "manufacturer": "Boeing",              // Who made it
  "model": "C-17A Globemaster III",      // Specific model
  "registration": "02-1110",             // Tail number
  "category": "Military Transport"       // Aircraft category
}
```

## 🗃️ **Database Options Analysis**

### **Option 1: AeroDataBox API** ⭐ **Recommended**

**Coverage**: Complete global aircraft database
**Cost**: $19/month for 10,000 requests
**API Endpoint**: `GET /aircrafts/icao24/{icao24}`

**Sample Response**:
```json
{
  "icao24": "ae117c",
  "registration": "02-1110", 
  "manufacturerName": "Boeing",
  "model": "C-17A Globemaster III",
  "typecode": "C17",
  "operatorName": "United States Air Force"
}
```

**Pros**:
- ✅ Professional aviation data
- ✅ Covers military and civilian aircraft
- ✅ Real-time updates
- ✅ Reliable ICAO type codes
- ✅ Official manufacturer data

**Cons**:
- ❌ $19/month cost
- ❌ API dependency

### **Option 2: OpenSky Aircraft Database** 

**Coverage**: Partial (weak on military aircraft)
**Cost**: Free
**API Endpoint**: `GET /api/metadata/aircraft/icao/{icao24}`

**Sample Response**:
```json
{
  "icao24": "ae117c",
  "registration": "02-1110",
  "manufacturername": "BOEING", 
  "model": "C-17A",
  "typecode": "C17"
}
```

**Pros**:
- ✅ Free
- ✅ Some coverage for known aircraft

**Cons**:
- ❌ Incomplete database
- ❌ Especially weak on military aircraft
- ❌ Inconsistent data quality

### **Option 3: Static Database**

**Coverage**: Only aircraft we manually add
**Cost**: Free (but requires manual work)
**Implementation**: JSON file with known mappings

**Sample Data**:
```json
{
  "aircraft_database": {
    "ae117c": {"type": "C17", "name": "C-17A Globemaster III"},
    "ae1462": {"type": "C17", "name": "C-17A Globemaster III"},
    "800375": {"type": "F16", "name": "F-16C Fighting Falcon"}
  }
}
```

**Pros**:
- ✅ Free
- ✅ Complete control over data
- ✅ Fast lookups (no API calls)

**Cons**:
- ❌ Manual maintenance required
- ❌ Limited coverage
- ❌ Need to research ICAO24 ranges

## 🔄 **Database Integration Flow**

### **Current Broken Flow**:
```
1. Get live aircraft from OpenSky
2. Check if callsign contains search term
3. Miss most aircraft because callsigns don't match
```

### **Correct Flow with Database**:
```
1. Get live aircraft from OpenSky
2. For each ICAO24: Look up aircraft type in database  
3. Filter aircraft where type matches search criteria
4. Return all matching aircraft regardless of callsign
```

## 💾 **Caching Strategy**

**Problem**: Looking up aircraft type for every flight is expensive

**Solution**: Smart caching system
```json
{
  "cache": {
    "ae117c": {
      "type": "C17",
      "name": "C-17A Globemaster III", 
      "cached_at": "2025-10-16T10:30:00Z",
      "ttl": "30 days"
    }
  }
}
```

**Benefits**:
- Only lookup unknown ICAO24 codes
- Cache results for 30 days (aircraft don't change type)
- Minimize API costs while maintaining accuracy

## 📊 **Cost Analysis**

### **AeroDataBox Scenario**:
- **Monthly cost**: $19
- **Requests**: 10,000/month
- **Usage pattern**: ~100 new ICAO24s per day = 3,000/month
- **Buffer**: 7,000 requests for retries/updates
- **Cost per aircraft identified**: $0.006

### **OpenSky + Manual Scenario**:
- **Monthly cost**: $0
- **Coverage**: ~30% of aircraft (estimate)
- **Maintenance time**: 2-3 hours/month researching aircraft
- **Hidden cost**: Development time and incomplete coverage

## 🎯 **Recommendation Matrix**

| Use Case | Recommended Solution | Reasoning |
|----------|---------------------|-----------|
| **Serious military tracking** | AeroDataBox | Complete coverage, professional data |
| **Hobby/learning project** | OpenSky + Static | Free, covers common cases |
| **Production system** | AeroDataBox | Reliability and coverage critical |
| **Budget constrained** | Static database | Manual work but functional |

## 🚀 **Implementation Priority**

### **Phase 1: Proof of Concept (Free)**
- Test OpenSky aircraft database with known ICAO24s
- Build small static database for C-17s we've seen
- Verify structured search works vs substring

### **Phase 2: Production Ready (Paid)**
- Integrate AeroDataBox API
- Implement caching system
- Test with full range of military aircraft

### **Phase 3: Optimization**
- Coverage analytics
- Cost optimization
- Hybrid approach (static + API)

## 📋 **API Research Tasks**

When resuming project:

1. **Test AeroDataBox API**:
   - Sign up for free trial
   - Test with known ICAO24s: "ae117c", "ae1462"
   - Verify C-17 detection accuracy

2. **Test OpenSky Aircraft DB**:
   - Try endpoint with same ICAO24s
   - Compare coverage vs AeroDataBox
   - Document gaps

3. **Research ICAO24 Ranges**:
   - US military aircraft ranges
   - Pattern recognition for aircraft types
   - Build initial static database

## 💡 **Success Metrics**

**Before database integration**:
- ❌ Search "globemaster" → 0 results (missed RCH4231)
- ❌ 578 false positives from substring search

**After database integration**:
- ✅ Search "globemaster" → All C-17s globally
- ✅ Zero false positives
- ✅ Reliable aircraft type identification

The database integration is the **key enabler** for professional-grade aircraft search.