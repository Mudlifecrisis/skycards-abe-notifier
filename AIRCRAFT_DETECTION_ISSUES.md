# Aircraft Detection Issues & Analysis

*Session Date: October 15, 2025*

## 🚨 **Core Problems Identified**

### **Problem 1: Coverage Gap Between Data Sources**

**Issue**: Aircraft visible on ADSBExchange but missing from OpenSky Network
- **Example**: RCH4231 (Hex: AE117C) - Boeing C-17A Globemaster III
- **Visible on**: ADSBExchange.com ✅
- **Missing from**: OpenSky Network API ❌

**Root Cause Analysis**:
- **Different receiver networks**: ADSBExchange vs OpenSky use different volunteer ADS-B receivers
- **Military aircraft filtering**: OpenSky may filter out certain military flights for security
- **Geographic coverage**: OpenSky has gaps in certain regions
- **Timing differences**: Aircraft may move out of OpenSky coverage quickly

**Impact**: Users can see aircraft on websites but our bot doesn't detect them

### **Problem 2: User Experience - Hex Codes vs Friendly Names**

**Issue**: Search terms don't match how users think
- **Users want to search**: "globemaster", "f16", "warthog"
- **System requires**: "AE117C", "RCH4231", specific callsigns
- **OpenSky only provides**: ICAO24 hex codes, callsigns, country

**Data Structure Limitations**:
```json
{
  "icao24": "ae1462",
  "callsign": "RCH3241", 
  "origin_country": "United States",
  // NO aircraft type information
}
```

**What's Missing**:
- Aircraft type: "C-17A"
- Manufacturer: "Boeing"
- Common names: "Globemaster III"
- Nicknames: "Warthog", "Viper", etc.

## ✅ **Current Working Status**

### **Successfully Fixed Tonight**:
1. **OpenSky Authentication**: Added fallback to anonymous access when credentials fail
2. **Quiet Hours Bug**: Fixed hardcoded vs environment variable conflict
3. **Rare Aircraft Detection**: Now finding 3 RCH aircraft (RCH3241, RCH183, RCH808)
4. **Data Parsing**: Altitude and speed conversion working correctly

### **Current Detection Results**:
```
RCH3241 (matched: RCH) - 37,000ft, 506kts
RCH183 (matched: RCH) - 31,025ft, 462kts  
RCH808 (matched: RCH) - 33,000ft, 499kts
```

### **What Works**:
- OpenSky API connection (anonymous)
- Search term matching for callsigns
- Multi-user airport monitoring
- Alert acknowledgment system
- Mission search functionality
- Comprehensive help system (`!`)

## 🔍 **Technical Details**

### **API Comparison**:
| Feature | OpenSky Network | ADSBExchange |
|---------|----------------|--------------|
| Coverage | Academic/volunteer | Commercial aggregator |
| Military aircraft | Some filtered | Less filtering |
| Rate limits | 4,000/day free | Varies by tier |
| Data quality | High | High |
| Real-time | Good | Excellent |
| Cost | Free | Free tier + paid |

### **Data Sources Available**:
1. **OpenSky Network** (current)
   - Free tier: 4,000 calls/day
   - Anonymous access working
   - Some military aircraft missing

2. **ADSBExchange**
   - Better military coverage
   - Multiple API tiers
   - Broader receiver network

3. **AeroDataBox**
   - Aircraft database with types
   - Commercial API
   - Good for civilian aircraft

## 🎯 **User Impact**

### **Current User Experience**:
- ❌ Missing aircraft they can see on websites
- ❌ Have to guess obscure search terms
- ✅ Reliable detection for aircraft that are in OpenSky
- ✅ Multi-user system works well
- ✅ Alert system is comprehensive

### **Desired User Experience**:
- ✅ Find all aircraft visible on flight tracking sites
- ✅ Search with intuitive terms like "globemaster"
- ✅ See aircraft type in alerts: "RCH4231 (C-17A Globemaster III)"
- ✅ Get suggestions for related aircraft types

## 📊 **Success Metrics**

### **Coverage**:
- Current: ~75% of military aircraft (estimated)
- Goal: >95% of publicly visible military aircraft

### **Usability**:
- Current: Requires technical knowledge of callsigns
- Goal: Natural language search terms

### **Reliability**:
- Current: Solid when aircraft is in OpenSky
- Goal: Consistent across all major flight tracking sources

## 🚧 **Next Session Priorities**

1. **Research ADSBExchange API options** - evaluate cost/benefit
2. **Create aircraft type database** - map ICAO24 codes to types
3. **Test dual-source approach** - ADSBExchange + OpenSky
4. **Improve search UX** - allow "globemaster" searches

## 🚨 **MAJOR UPDATE - October 16, 2025**

### **Core Problem Identified Through User Testing**

**Discovery**: User searched "C17" on OpenSky website → 578 results, 99% false matches
**Root Cause**: Substring text matching instead of structured aircraft type filtering

### **Technical Evidence**
- OpenSky API provides ICAO24 and callsign but **NO aircraft type information**
- Current system matches "GLOBEMASTER" against callsign "RCH4231" → no match
- Missing database: ICAO24 → aircraft type mapping

### **Professional Solution Identified**
- **AeroDataBox API**: $19/month for complete aircraft database
- **Structured search**: "globemaster" → "C17" → filter by aircraft type
- **Expected result**: Find ALL C-17s globally, zero false positives

### **Implementation Status**
- ✅ Problem fully understood and documented
- ✅ Professional solution researched (AeroDataBox)
- ✅ Architecture designed for structured search
- 🚧 Ready for implementation when project resumes

## 📝 **Notes for Project Resume**

- All code fixes from previous session are working
- Authentication issues resolved  
- **NEW**: Core search logic breakthrough achieved
- **PRIORITY**: Implement AeroDataBox integration for aircraft identification
- **OUTCOME**: Professional-grade aircraft tracking system