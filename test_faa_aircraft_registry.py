#!/usr/bin/env python3
"""
Test FAA Aircraft Registry database download and analysis
"""
import asyncio
import aiohttp
import csv
import json
from io import StringIO
import zipfile
import os

async def download_faa_registry():
    """Download and analyze FAA Aircraft Registry database"""
    
    print("Testing FAA Aircraft Registry Database")
    print("=" * 50)
    
    # FAA aircraft registry download URL
    faa_url = "https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download"
    
    print("Step 1: Checking FAA aircraft registry page...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(faa_url) as response:
                print(f"FAA Page Status: {response.status}")
                
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Look for download links in the HTML
                    if "MASTER.txt" in html_content or "master.txt" in html_content:
                        print("✅ Found aircraft master file references")
                        
                        # Try common download URLs based on FAA structure
                        download_urls = [
                            "https://registry.faa.gov/database/ReleasableAircraft.zip",
                            "https://registry.faa.gov/database/master.txt",
                            "https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/media/master.txt"
                        ]
                        
                        for download_url in download_urls:
                            print(f"\nTrying download URL: {download_url}")
                            
                            try:
                                async with session.get(download_url) as dl_response:
                                    print(f"Download Status: {dl_response.status}")
                                    
                                    if dl_response.status == 200:
                                        content_type = dl_response.headers.get('Content-Type', '')
                                        content_length = dl_response.headers.get('Content-Length', 'unknown')
                                        
                                        print(f"Content-Type: {content_type}")
                                        print(f"Content-Length: {content_length} bytes")
                                        
                                        if 'zip' in content_type or download_url.endswith('.zip'):
                                            print("Found ZIP file - would need to extract")
                                            # For demo, just analyze headers
                                            data = await dl_response.read()
                                            print(f"Downloaded {len(data)} bytes")
                                            
                                        elif 'text' in content_type or download_url.endswith('.txt'):
                                            print("Found text file - analyzing sample...")
                                            
                                            # Read first 10KB to analyze structure
                                            sample_data = ""
                                            async for chunk in dl_response.content.iter_chunked(1024):
                                                sample_data += chunk.decode('utf-8', errors='ignore')
                                                if len(sample_data) > 10000:
                                                    break
                                            
                                            print(f"Sample data length: {len(sample_data)} chars")
                                            
                                            # Analyze CSV structure
                                            lines = sample_data.split('\n')[:10]
                                            print("First 5 lines:")
                                            for i, line in enumerate(lines[:5]):
                                                print(f"  {i+1}: {line[:100]}...")
                                            
                                            # Try to parse as CSV
                                            try:
                                                csv_reader = csv.reader(StringIO(sample_data))
                                                headers = next(csv_reader)
                                                print(f"\nCSV Headers ({len(headers)} columns):")
                                                for i, header in enumerate(headers):
                                                    if i < 20:  # Show first 20 headers
                                                        print(f"  {i+1}: {header}")
                                                    elif i == 20:
                                                        print(f"  ... and {len(headers)-20} more columns")
                                                        break
                                                
                                                # Show sample record
                                                try:
                                                    sample_record = next(csv_reader)
                                                    print(f"\nSample record:")
                                                    for i, (header, value) in enumerate(zip(headers, sample_record)):
                                                        if i < 10:  # Show first 10 fields
                                                            print(f"  {header}: {value}")
                                                        elif i == 10:
                                                            print(f"  ... and {len(sample_record)-10} more fields")
                                                            break
                                                except StopIteration:
                                                    print("No sample record available")
                                                    
                                            except Exception as csv_error:
                                                print(f"CSV parsing error: {csv_error}")
                                        
                                        # Success - we found downloadable data
                                        return True
                                        
                            except Exception as dl_error:
                                print(f"Download error: {dl_error}")
                    
                    else:
                        print("❌ No aircraft master file references found")
                        print("Checking page content for other download links...")
                        
                        # Look for other download patterns
                        if "download" in html_content.lower():
                            print("Found 'download' mentions in page")
                        
    except Exception as e:
        print(f"Error accessing FAA registry: {e}")
    
    return False

async def test_github_faa_tools():
    """Test GitHub tools for FAA aircraft registry"""
    
    print("\n" + "=" * 50)
    print("Testing GitHub FAA Aircraft Registry Tools")
    
    # GitHub repository mentioned in search results
    github_repo = "https://api.github.com/repos/ClearAerospace/faa-aircraft-registry"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(github_repo) as response:
                if response.status == 200:
                    repo_data = await response.json()
                    
                    print(f"✅ Found GitHub repo: {repo_data['name']}")
                    print(f"Description: {repo_data['description']}")
                    print(f"Stars: {repo_data['stargazers_count']}")
                    print(f"Language: {repo_data['language']}")
                    print(f"Updated: {repo_data['updated_at']}")
                    
                    # Check README for usage instructions
                    readme_url = f"https://api.github.com/repos/ClearAerospace/faa-aircraft-registry/readme"
                    async with session.get(readme_url) as readme_response:
                        if readme_response.status == 200:
                            readme_data = await readme_response.json()
                            print("✅ Found README with usage instructions")
                        
                else:
                    print(f"GitHub repo not accessible: {response.status}")
                    
    except Exception as e:
        print(f"Error checking GitHub tools: {e}")

if __name__ == "__main__":
    asyncio.run(download_faa_registry())
    asyncio.run(test_github_faa_tools())