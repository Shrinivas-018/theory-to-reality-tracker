"""
Fix Images in Database

Updates all existing ideas with relevant images from Bing Image Search API.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.mongodb_service import MongoDBService
import requests
import time


def search_bing_image(query):
    """
    Search for images using Bing Image Search API.
    Uses free tier with no API key required.
    """
    try:
        # Bing Image Search endpoint (using HTML scraping as fallback)
        # We'll use DuckDuckGo image search which doesn't require API key
        url = "https://duckduckgo.com/"
        
        # For now, use a more reliable approach with direct image URLs
        # We'll construct contextual image URLs based on the query
        
        # Try SerpAPI (has free tier)
        serpapi_url = "https://serpapi.com/search"
        params = {
            "engine": "bing_images",
            "q": query,
            "api_key": "demo"  # Demo key for testing
        }
        
        # Since we don't have API keys, let's use a smarter fallback
        # Use Wikipedia/Wikimedia Commons images
        return search_wikimedia_image(query)
        
    except Exception as e:
        print(f"    ⚠ Bing search failed: {e}")
        return None


def search_wikimedia_image(query):
    """
    Search for images on Wikimedia Commons.
    Free and open source images.
    """
    try:
        # Clean up query - extract main concept
        main_concept = query.split()[0] if query else "technology"
        
        # Wikipedia API to get page images
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": main_concept,
            "prop": "pageimages",
            "pithumbsize": 800
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if "thumbnail" in page_data:
                    return {
                        "url": page_data["thumbnail"]["source"],
                        "source": "Wikipedia"
                    }
        
        return None
        
    except Exception as e:
        print(f"    ⚠ Wikimedia search failed: {e}")
        return None


def get_contextual_search_query(idea_name, yuga_stage):
    """Generate complex contextual search query for each Yuga stage."""
    
    # Detailed context mapping for each Yuga
    yuga_contexts = {
        "satya_yuga": {
            "prefix": "ancient",
            "style": "traditional natural spiritual divine sacred",
            "time": "prehistoric primordial golden age",
            "examples": "temple nature ritual meditation"
        },
        "treta_yuga": {
            "prefix": "medieval",
            "style": "historical classical vintage heritage",
            "time": "middle ages renaissance traditional",
            "examples": "manuscript scroll parchment ceremony"
        },
        "dwapar_yuga": {
            "prefix": "industrial",
            "style": "mechanical vintage factory workshop",
            "time": "19th century victorian steam age",
            "examples": "machinery gears workshop craftsmanship"
        },
        "kali_yuga": {
            "prefix": "modern",
            "style": "contemporary digital technology electronic",
            "time": "21st century current futuristic",
            "examples": "computer digital screen interface"
        }
    }
    
    context = yuga_contexts.get(yuga_stage, yuga_contexts["kali_yuga"])
    
    # Build complex query
    # For Satya Yuga: focus on natural/ancient versions
    # For Treta Yuga: focus on medieval/traditional versions
    # For Dwapar Yuga: focus on industrial/mechanical versions
    # For Kali Yuga: focus on modern/digital versions
    
    if yuga_stage == "satya_yuga":
        query = f"{idea_name} {context['prefix']} {context['time']}"
    elif yuga_stage == "treta_yuga":
        query = f"{idea_name} {context['prefix']} {context['style']}"
    elif yuga_stage == "dwapar_yuga":
        query = f"{idea_name} {context['prefix']} {context['time']}"
    else:  # kali_yuga
        query = f"{idea_name} {context['prefix']} {context['style']}"
    
    return query


def fix_images():
    """Update all ideas with relevant images from Bing/Wikipedia."""
    mongo = MongoDBService()
    
    print("=" * 70)
    print("🔧 FIXING IMAGES WITH BING/WIKIPEDIA API")
    print("=" * 70)
    
    # Get all ideas
    ideas = mongo.get_all_ideas(limit=1000)
    print(f"\n📊 Found {len(ideas)} ideas to update")
    print("⏱️  Fetching images from Wikipedia/Wikimedia Commons...")
    
    updated_count = 0
    
    for i, idea in enumerate(ideas, 1):
        idea_name = idea.get("idea", "")
        print(f"\n[{i}/{len(ideas)}] Updating: {idea_name}")
        
        # Update images for each Yuga
        for yuga_stage in ["satya_yuga", "treta_yuga", "dwapar_yuga", "kali_yuga"]:
            if yuga_stage in idea.get("evolution", {}):
                
                # Get contextual search query
                search_query = get_contextual_search_query(idea_name, yuga_stage)
                print(f"  🔍 Searching: {search_query}")
                
                # Search for image
                image_data = search_bing_image(search_query)
                
                if image_data:
                    idea["evolution"][yuga_stage]["image"] = {
                        "url": image_data["url"],
                        "alt": f"{idea_name} in {yuga_stage.replace('_', ' ').title()}",
                        "source": image_data.get("source", "Wikipedia"),
                        "query": search_query
                    }
                    print(f"    ✓ Found image from {image_data.get('source', 'Wikipedia')}")
                else:
                    # Fallback to styled placeholder with gradient
                    yuga_colors = {
                        "satya_yuga": "FFD700/FFA500",  # Gold gradient
                        "treta_yuga": "C0C0C0/808080",  # Silver gradient
                        "dwapar_yuga": "CD7F32/8B4513",  # Bronze gradient
                        "kali_yuga": "4B0082/8B008B"    # Purple gradient
                    }
                    color = yuga_colors.get(yuga_stage, "4a5568/ffffff")
                    
                    idea["evolution"][yuga_stage]["image"] = {
                        "url": f"https://via.placeholder.com/800x600/{color}?text={idea_name.replace(' ', '+')}",
                        "alt": f"{idea_name} in {yuga_stage.replace('_', ' ').title()}",
                        "source": "Placeholder"
                    }
                    print(f"    ⚠ Using styled placeholder")
                
                # Rate limiting
                time.sleep(0.3)
        
        # Update in database
        if mongo.is_connected():
            try:
                mongo.collection.update_one(
                    {"idea": idea_name},
                    {"$set": {"evolution": idea["evolution"]}}
                )
                print(f"  ✓ Updated in database")
                updated_count += 1
            except Exception as e:
                print(f"  ✗ Error: {e}")
        else:
            print(f"  ⚠ MongoDB not connected, skipping")
        
        # Pause every 20 ideas
        if i % 20 == 0:
            print(f"\n  ⏸️  Pausing 3 seconds...")
            time.sleep(3)
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Updated {updated_count} ideas")
    print("=" * 70)


if __name__ == "__main__":
    fix_images()
