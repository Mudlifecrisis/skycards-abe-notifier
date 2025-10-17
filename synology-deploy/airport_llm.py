#!/usr/bin/env python3
"""
Airport LLM Assistant - Natural language airport discovery using DeepSeek
"""
import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class AirportLLMAssistant:
    def __init__(self):
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = "https://api.deepseek.com/v1/chat/completions"
        
        # Enhanced airport database with traffic info and specialties
        self.airport_database = {
            # Major International Hubs
            'DXB': {'name': 'Dubai International', 'city': 'Dubai', 'country': 'UAE', 'traffic': 'Very High', 'specialty': 'International hub, Emirates base'},
            'DWC': {'name': 'Dubai World Central', 'city': 'Dubai', 'country': 'UAE', 'traffic': 'Medium', 'specialty': 'Cargo focused, secondary hub'},
            'LHR': {'name': 'London Heathrow', 'city': 'London', 'country': 'UK', 'traffic': 'Very High', 'specialty': 'Major European hub, British Airways base'},
            'LGW': {'name': 'London Gatwick', 'city': 'London', 'country': 'UK', 'traffic': 'High', 'specialty': 'Secondary London airport'},
            'CDG': {'name': 'Paris Charles de Gaulle', 'city': 'Paris', 'country': 'France', 'traffic': 'Very High', 'specialty': 'Air France hub, major European gateway'},
            'FRA': {'name': 'Frankfurt am Main', 'city': 'Frankfurt', 'country': 'Germany', 'traffic': 'Very High', 'specialty': 'Lufthansa hub, cargo center'},
            'AMS': {'name': 'Amsterdam Schiphol', 'city': 'Amsterdam', 'country': 'Netherlands', 'traffic': 'Very High', 'specialty': 'KLM hub, European gateway'},
            'ICN': {'name': 'Seoul Incheon', 'city': 'Seoul', 'country': 'South Korea', 'traffic': 'Very High', 'specialty': 'Korean Air hub, Asian gateway'},
            'NRT': {'name': 'Tokyo Narita', 'city': 'Tokyo', 'country': 'Japan', 'traffic': 'Very High', 'specialty': 'International flights, JAL/ANA hub'},
            'HND': {'name': 'Tokyo Haneda', 'city': 'Tokyo', 'country': 'Japan', 'traffic': 'Very High', 'specialty': 'Domestic + some international'},
            
            # North American Major Hubs
            'JFK': {'name': 'John F Kennedy International', 'city': 'New York', 'country': 'USA', 'traffic': 'Very High', 'specialty': 'International gateway, multiple carriers'},
            'LAX': {'name': 'Los Angeles International', 'city': 'Los Angeles', 'country': 'USA', 'traffic': 'Very High', 'specialty': 'Pacific gateway, major hub'},
            'ORD': {'name': 'Chicago O\'Hare', 'city': 'Chicago', 'country': 'USA', 'traffic': 'Very High', 'specialty': 'American Airlines hub, central location'},
            'ATL': {'name': 'Atlanta Hartsfield-Jackson', 'city': 'Atlanta', 'country': 'USA', 'traffic': 'Very High', 'specialty': 'Delta hub, busiest airport'},
            'DFW': {'name': 'Dallas/Fort Worth', 'city': 'Dallas', 'country': 'USA', 'traffic': 'Very High', 'specialty': 'American Airlines main hub'},
            'MIA': {'name': 'Miami International', 'city': 'Miami', 'country': 'USA', 'traffic': 'High', 'specialty': 'Latin America gateway'},
            
            # Regional airports for reference
            'ABE': {'name': 'Lehigh Valley International', 'city': 'Allentown', 'country': 'USA', 'traffic': 'Low', 'specialty': 'Regional, limited commercial'},
            'PHL': {'name': 'Philadelphia International', 'city': 'Philadelphia', 'country': 'USA', 'traffic': 'High', 'specialty': 'American Airlines hub'},
            'EWR': {'name': 'Newark Liberty', 'city': 'Newark', 'country': 'USA', 'traffic': 'High', 'specialty': 'United hub, NYC area'},
            'BOS': {'name': 'Boston Logan', 'city': 'Boston', 'country': 'USA', 'traffic': 'High', 'specialty': 'JetBlue hub, European connections'},
            
            # Cargo/Military specialties
            'ANC': {'name': 'Anchorage Ted Stevens', 'city': 'Anchorage', 'country': 'USA', 'traffic': 'Medium', 'specialty': 'Major cargo hub, military traffic'},
            'MEM': {'name': 'Memphis International', 'city': 'Memphis', 'country': 'USA', 'traffic': 'Medium', 'specialty': 'FedEx main hub, cargo center'},
            'SDF': {'name': 'Louisville Muhammad Ali', 'city': 'Louisville', 'country': 'USA', 'traffic': 'Medium', 'specialty': 'UPS main hub, cargo center'},
        }
    
    async def ask_deepseek(self, query: str) -> str:
        """Query DeepSeek API for airport recommendations"""
        if not self.deepseek_api_key:
            return "DeepSeek API key not configured"
            
        # Create airport database context for the LLM
        airport_context = "\n".join([
            f"{code}: {info['name']} ({info['city']}, {info['country']}) - Traffic: {info['traffic']}, Specialty: {info['specialty']}"
            for code, info in self.airport_database.items()
        ])
        
        system_prompt = f"""You are an aviation expert helping users find the best airports for flight tracking. 

Available airports in database:
{airport_context}

When responding:
1. Suggest 1-3 specific airport codes that best match the request
2. Explain WHY each airport is recommended
3. Include traffic level and specialty information
4. Format as: CODE (Name) - Reason
5. Keep responses concise and practical
6. If the user asks about a location not in the database, provide the most likely IATA codes and explain you don't have detailed info

Example response format:
• DXB (Dubai International) - Highest traffic in Dubai, major Emirates hub
• DWC (Dubai World Central) - Secondary option, more cargo focused"""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
                
                async with session.post(self.deepseek_base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content'].strip()
                    else:
                        return f"DeepSeek API error: {response.status}"
                        
        except Exception as e:
            return f"Error querying DeepSeek: {str(e)}"
    
    def get_airport_info(self, airport_code: str) -> Optional[Dict]:
        """Get detailed info about a specific airport"""
        return self.airport_database.get(airport_code.upper())
    
    def search_airports_by_keyword(self, keyword: str) -> List[Dict]:
        """Search airports by city, country, or name keyword"""
        keyword = keyword.lower()
        results = []
        
        for code, info in self.airport_database.items():
            if (keyword in info['name'].lower() or 
                keyword in info['city'].lower() or 
                keyword in info['country'].lower() or
                keyword in info['specialty'].lower()):
                results.append({'code': code, **info})
                
        return results

if __name__ == "__main__":
    async def test_airport_llm():
        assistant = AirportLLMAssistant()
        
        # Test queries
        test_queries = [
            "find dubai airport with highest traffic",
            "best european airport for boeing 777s",
            "airport near london with international flights",
            "what's the code for paris airport"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            response = await assistant.ask_deepseek(query)
            print(f"Response: {response}")
    
    asyncio.run(test_airport_llm())