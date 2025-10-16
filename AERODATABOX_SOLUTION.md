# AeroDataBox Solution Research

*Session Date: October 16, 2025*

## 🎯 **Why AeroDataBox is the Professional Solution**

AeroDataBox provides the **missing aircraft type database** that our system needs to properly identify aircraft beyond just ICAO24 hex codes and callsigns.

## 📊 **Service Overview**

**Company**: AeroDataBox (Professional aviation data provider)
**Website**: https://aerodatabox.com/
**Primary Use**: Aircraft database, airport data, flight tracking
**Reliability**: Used by aviation professionals and commercial applications

## 💰 **Pricing Analysis**

### **Starter Plan - $19/month**
- **10,000 API requests per month**
- **Aircraft database access**
- **Real-time flight data**
- **Airport information**

### **Usage Calculation for Our System**:
```
Scenario: 3 users, active aircraft tracking
- New ICAO24 encounters: ~100 per day
- Monthly aircraft lookups: ~3,000
- Buffer for retries/updates: 7,000
- Total usage: Well within 10,000 limit
```

**Cost per aircraft identified**: $0.006 (less than a penny)

## 🔧 **API Integration Points**

### **Primary Endpoint: Aircraft Information**
```
GET https://aerodatabox.p.rapidapi.com/aircrafts/icao24/{icao24}
```

**Example Request**:
```bash
curl -X GET \
  "https://aerodatabox.p.rapidapi.com/aircrafts/icao24/ae117c" \
  -H "X-RapidAPI-Key: YOUR_KEY" \
  -H "X-RapidAPI-Host: aerodatabox.p.rapidapi.com"
```

**Example Response**:
```json
{
  "icao24": "ae117c",
  "registration": "02-1110",
  "manufacturerName": "Boeing",
  "model": "C-17A Globemaster III",
  "typecode": "C17",
  "operatorName": "United States Air Force",
  "operatorIcao": "RCH",
  "operatorIata": "",
  "owner": "United States Air Force",
  "categoryDescription": "Military Transport"
}
```

### **Key Data Fields for Our System**:
- **`typecode`**: "C17" (ICAO aircraft type - our main filter)
- **`model`**: "C-17A Globemaster III" (for user display)
- **`manufacturerName`**: "Boeing" (for manufacturer searches)
- **`operatorName`**: "United States Air Force" (for military identification)

## 🔄 **Integration Architecture**

### **Caching Layer Design**:
```python
class AircraftDatabase:
    def __init__(self):
        self.cache = {}  # ICAO24 -> aircraft info
        self.cache_file = "aircraft_cache.json"
        
    async def get_aircraft_info(self, icao24: str):
        # Check cache first
        if icao24 in self.cache:
            return self.cache[icao24]
            
        # Call AeroDataBox API
        info = await self.fetch_from_aerodatabox(icao24)
        
        # Cache result (aircraft type doesn't change)
        self.cache[icao24] = info
        self.save_cache()
        
        return info
```

### **Search Logic Integration**:
```python
async def find_aircraft_by_type(self, search_term: str):
    # Translate user term to ICAO type
    icao_type = self.translate_search_term(search_term)  # "globemaster" -> "C17"
    
    # Get all live aircraft
    live_aircraft = await self.fetch_live_aircraft()
    
    # Filter by aircraft type
    matching_aircraft = []
    for aircraft in live_aircraft:
        # Look up aircraft type
        aircraft_info = await self.aircraft_db.get_aircraft_info(aircraft['icao24'])
        
        # Check if type matches
        if aircraft_info and aircraft_info.get('typecode') == icao_type:
            # Combine live data with aircraft info
            enhanced_aircraft = {**aircraft, **aircraft_info}
            matching_aircraft.append(enhanced_aircraft)
    
    return matching_aircraft
```

## 🎯 **Expected Results**

### **Before AeroDataBox**:
```bash
User: "!add globemaster"
Search: Look for "GLOBEMASTER" in callsign
Result: ❌ 0 matches (RCH4231 callsign doesn't contain "GLOBEMASTER")
```

### **After AeroDataBox**:
```bash
User: "!add globemaster" 
System: "globemaster" -> ICAO type "C17"
Search: Filter all aircraft where typecode == "C17"
Result: ✅ All C-17 Globemaster III aircraft globally, including:
  - RCH4231 (ae117c) - Boeing C-17A Globemaster III
  - RCH808 (ae119c) - Boeing C-17A Globemaster III  
  - Any other C-17s currently flying
```

## 🔒 **API Security & Rate Limiting**

### **Authentication**:
- Uses RapidAPI marketplace
- Requires API key in headers
- Standard OAuth2 or API key authentication

### **Rate Limiting**:
- 10,000 requests/month on Starter plan
- Built-in rate limiting on their side
- Our caching reduces actual API calls

### **Error Handling**:
```python
async def fetch_from_aerodatabox(self, icao24: str):
    try:
        response = await self.api_call(icao24)
        if response.status == 200:
            return await response.json()
        elif response.status == 404:
            # Aircraft not in database
            return None
        elif response.status == 429:
            # Rate limited - implement backoff
            await asyncio.sleep(60)
            return await self.fetch_from_aerodatabox(icao24)
    except Exception as e:
        # Log error, return None to gracefully degrade
        print(f"AeroDataBox API error: {e}")
        return None
```

## 📊 **Coverage Comparison**

| Aircraft Type | AeroDataBox | OpenSky DB | Static DB |
|---------------|-------------|------------|-----------|
| **Military** | ✅ Excellent | ❌ Poor | ⚠️ Manual |
| **Commercial** | ✅ Complete | ✅ Good | ❌ Missing |
| **Private** | ✅ Complete | ⚠️ Partial | ❌ Missing |
| **Experimental** | ✅ Good | ❌ Poor | ❌ Missing |

## 🚀 **Implementation Plan**

### **Phase 1: API Testing (1 hour)**
```bash
# Test with known aircraft
curl -X GET "https://aerodatabox.p.rapidapi.com/aircrafts/icao24/ae117c"
curl -X GET "https://aerodatabox.p.rapidapi.com/aircrafts/icao24/ae1462"
curl -X GET "https://aerodatabox.p.rapidapi.com/aircrafts/icao24/ae119c"
```

### **Phase 2: Cache System (2 hours)**
- Implement aircraft info caching
- Add cache persistence (JSON file)
- Add cache invalidation (30-day TTL)

### **Phase 3: Search Integration (2 hours)**
- Update rare hunter to use aircraft database
- Implement type-based filtering
- Add user-friendly alias system

### **Phase 4: Testing (1 hour)**
- Test "globemaster" search end-to-end
- Verify all C-17s are found
- Confirm no false positives

## 💡 **Alternative Implementation**

### **Hybrid Approach** (Cost-Conscious):
1. **Static database** for common military aircraft (C-17, F-16, etc.)
2. **AeroDataBox API** for unknown civilian aircraft
3. **Graceful fallback** when API unavailable

```python
async def get_aircraft_info(self, icao24: str):
    # Check static database first (free)
    if icao24 in self.static_database:
        return self.static_database[icao24]
    
    # Check cache
    if icao24 in self.cache:
        return self.cache[icao24]
    
    # Use API for unknown aircraft
    return await self.fetch_from_aerodatabox(icao24)
```

## 📋 **Next Steps When Resuming**

1. **Sign up for AeroDataBox trial**
2. **Test API with known ICAO24 codes** (ae117c, ae1462, ae119c)
3. **Verify C-17 identification accuracy**
4. **Implement caching layer**
5. **Integration with existing rare hunter**
6. **End-to-end testing with "globemaster" search**

AeroDataBox solves our **core aircraft identification problem** with professional-grade data at minimal cost.