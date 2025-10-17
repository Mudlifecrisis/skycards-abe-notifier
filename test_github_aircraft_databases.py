#!/usr/bin/env python3
"""
Test GitHub aircraft database repositories
"""
import asyncio
import aiohttp
import json
import csv
from io import StringIO

async def test_github_aircraft_databases():
    """Test various GitHub aircraft database repositories"""
    
    print("Testing GitHub Aircraft Database Repositories")
    print("=" * 60)
    
    repositories = [
        {
            "name": "junzis/aircraft-db",
            "description": "Query all types of flight identities",
            "api_url": "https://api.github.com/repos/junzis/aircraft-db"
        },
        {
            "name": "atoff/OpenAircraftType", 
            "description": "Open-source aircraft type database",
            "api_url": "https://api.github.com/repos/atoff/OpenAircraftType"
        },
        {
            "name": "sdr-enthusiasts/plane-alert-db",
            "description": "List of interesting aircraft",
            "api_url": "https://api.github.com/repos/sdr-enthusiasts/plane-alert-db"
        }
    ]
    
    for repo in repositories:
        print(f"\n--- {repo['name']} ---")
        print(f"Description: {repo['description']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get repository info
                async with session.get(repo['api_url']) as response:
                    if response.status == 200:
                        repo_data = await response.json()
                        
                        print(f"Stars: {repo_data['stargazers_count']}")
                        print(f"Language: {repo_data.get('language', 'Unknown')}")
                        print(f"Size: {repo_data['size']} KB")
                        print(f"Updated: {repo_data['updated_at'][:10]}")
                        
                        # Get contents to look for data files
                        contents_url = repo_data['contents_url'].replace('{+path}', '')
                        async with session.get(contents_url) as contents_response:
                            if contents_response.status == 200:
                                contents = await contents_response.json()
                                
                                print("Repository contents:")
                                data_files = []
                                for item in contents:
                                    print(f"  {item['name']} ({item['type']})")
                                    
                                    # Look for data files
                                    if (item['type'] == 'file' and 
                                        any(ext in item['name'].lower() for ext in ['.csv', '.json', '.txt', '.db'])):
                                        data_files.append(item)
                                
                                # Test downloading sample data files
                                if data_files:
                                    print(f"\nFound {len(data_files)} data files:")
                                    for data_file in data_files[:3]:  # Test first 3
                                        print(f"\nTesting: {data_file['name']}")
                                        
                                        try:
                                            file_url = data_file['download_url']
                                            async with session.get(file_url) as file_response:
                                                if file_response.status == 200:
                                                    # Get file size
                                                    content_length = file_response.headers.get('Content-Length', 'unknown')
                                                    print(f"  Size: {content_length} bytes")
                                                    
                                                    # Sample first 2KB
                                                    sample_data = ""
                                                    bytes_read = 0
                                                    async for chunk in file_response.content.iter_chunked(512):
                                                        chunk_text = chunk.decode('utf-8', errors='ignore')
                                                        sample_data += chunk_text
                                                        bytes_read += len(chunk)
                                                        if bytes_read > 2048:  # 2KB sample
                                                            break
                                                    
                                                    print(f"  Sample content ({len(sample_data)} chars):")
                                                    
                                                    # Analyze format
                                                    if data_file['name'].endswith('.csv'):
                                                        try:
                                                            csv_reader = csv.reader(StringIO(sample_data))
                                                            headers = next(csv_reader)
                                                            print(f"    CSV Headers: {headers}")
                                                            
                                                            # Look for ICAO24 and type fields
                                                            icao_fields = [h for h in headers if 'icao' in h.lower()]
                                                            type_fields = [h for h in headers if any(word in h.lower() for word in ['type', 'model', 'aircraft'])]
                                                            
                                                            if icao_fields:
                                                                print(f"    ICAO fields: {icao_fields}")
                                                            if type_fields:
                                                                print(f"    Type fields: {type_fields}")
                                                            
                                                            # Show sample record
                                                            try:
                                                                sample_record = next(csv_reader)
                                                                print(f"    Sample record: {sample_record[:5]}...")
                                                            except StopIteration:
                                                                pass
                                                                
                                                        except Exception as csv_error:
                                                            print(f"    CSV parse error: {csv_error}")
                                                    
                                                    elif data_file['name'].endswith('.json'):
                                                        try:
                                                            data = json.loads(sample_data)
                                                            if isinstance(data, list) and data:
                                                                print(f"    JSON array with {len(data)} items")
                                                                sample_item = data[0]
                                                                print(f"    Sample keys: {list(sample_item.keys())}")
                                                            elif isinstance(data, dict):
                                                                print(f"    JSON object with keys: {list(data.keys())}")
                                                        except Exception as json_error:
                                                            print(f"    JSON parse error: {json_error}")
                                                    
                                                    else:
                                                        # Show first few lines
                                                        lines = sample_data.split('\n')[:5]
                                                        for i, line in enumerate(lines):
                                                            print(f"    Line {i+1}: {line[:80]}...")
                                                
                                        except Exception as file_error:
                                            print(f"  Error downloading {data_file['name']}: {file_error}")
                                
                                else:
                                    print("No data files found")
                    else:
                        print(f"Repository not accessible: {response.status}")
                        
        except Exception as e:
            print(f"Error testing {repo['name']}: {e}")
        
        await asyncio.sleep(1)  # Rate limiting

if __name__ == "__main__":
    asyncio.run(test_github_aircraft_databases())