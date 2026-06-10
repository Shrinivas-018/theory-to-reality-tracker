"""
Complete All Rich Content for Yugas

This script:
1. Checks API credits before starting
2. Updates all remaining ideas (88/109)
3. Shows progress and estimates
4. Handles errors gracefully
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.mongodb_service import MongoDBService
from backend.services.yuga_generator import YugaGeneratorService
import requests
import time


def check_api_credits():
    """Check OpenRouter API credits."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY")
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://openrouter.ai/api/v1/credits", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_credits = data.get("data", {}).get("total_credits", 0)
            total_usage = data.get("data", {}).get("total_usage", 0)
            remaining = total_credits - total_usage
            
            print(f"💰 API Credits:")
            print(f"   Total: ${total_credits:.4f}")
            print(f"   Used: ${total_usage:.4f}")
            print(f"   Remaining: ${remaining:.4f}")
            
            return remaining
        else:
            print(f"⚠️  Could not check credits (Status: {response.status_code})")
            return None
            
    except Exception as e:
        print(f"⚠️  Error checking credits: {e}")
        return None


def has_rich_content(idea: dict) -> bool:
    """Check if idea already has rich content."""
    evolution = idea.get("evolution", {})
    if not evolution:
        return False
    
    # Check if any Yuga has time_period field
    for yuga in ["satya_yuga", "treta_yuga", "dwapar_yuga", "kali_yuga"]:
        if yuga in evolution:
            if "time_period" in evolution[yuga]:
                return True
    
    return False


def generate_rich_evolution(idea_name: str, description: str) -> dict:
    """Generate rich, detailed evolution content."""
    yuga_gen = YugaGeneratorService()
    
    try:
        # The yuga_generator now automatically adds rich content
        evolution = yuga_gen.generate_yuga_evolution(idea_name, description, rich_content=True)
        return evolution
    except Exception as e:
        print(f"  ✗ API Error: {e}")
        return None


def main():
    """Complete all ideas with rich content."""
    mongo = MongoDBService()
    
    print("=" * 70)
    print("🔄 COMPLETE ALL RICH CONTENT FOR YUGAS")
    print("=" * 70)
    
    # Check API credits first
    print("\n📊 Checking API Status...")
    print("   Using: openai/gpt-oss-120b:free (FREE MODEL)")
    print("   No credits required! ✅")
    
    print("\n" + "=" * 70)
    
    # Get all ideas
    ideas = mongo.get_all_ideas(limit=1000)
    print(f"\n📊 Found {len(ideas)} total ideas")
    
    # Filter ideas that need rich content
    ideas_to_update = [idea for idea in ideas if not has_rich_content(idea)]
    ideas_already_done = len(ideas) - len(ideas_to_update)
    
    print(f"✅ Already have rich content: {ideas_already_done}")
    print(f"⏳ Need to update: {len(ideas_to_update)}")
    
    if len(ideas_to_update) == 0:
        print("\n🎉 All ideas already have rich content!")
        return
    
    # Estimate time (free model is slower)
    estimated_time = len(ideas_to_update) * 5  # ~5 seconds per idea for free model
    
    print(f"\n⏱️  Estimated time: {estimated_time // 60} minutes {estimated_time % 60} seconds")
    print("   (Free model may be slower but costs nothing!)")
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return
    
    print("\n⏱️  Starting generation...\n")
    
    updated_count = 0
    failed_count = 0
    
    for i, idea in enumerate(ideas_to_update, 1):
        idea_name = idea.get("idea", "")
        description = idea.get("description", "")
        
        print(f"[{i}/{len(ideas_to_update)}] Generating: {idea_name}")
        
        try:
            # Generate rich evolution
            rich_evolution = generate_rich_evolution(idea_name, description)
            
            if rich_evolution is None:
                print(f"  ⚠️  Skipped due to API error")
                failed_count += 1
                
                # Check if it's a credit issue
                if failed_count >= 3:
                    print("\n⚠️  Multiple failures detected. Checking credits...")
                    remaining = check_api_credits()
                    if remaining is not None and remaining <= 0:
                        print("\n❌ OUT OF CREDITS!")
                        print(f"   Completed: {updated_count}/{len(ideas_to_update)}")
                        print("   Add more credits and run again to continue.")
                        break
                
                continue
            
            # Update in database
            if mongo.is_connected():
                mongo.collection.update_one(
                    {"idea": idea_name},
                    {"$set": {"evolution": rich_evolution}}
                )
                updated_count += 1
                print(f"  ✓ Updated with rich content")
            
            # Rate limiting (longer for free model)
            time.sleep(2)
            
            # Pause every 5 ideas (free model needs more breaks)
            if i % 5 == 0:
                print(f"\n  ⏸️  Pausing 10 seconds (free model rate limit)...")
                time.sleep(10)
                print()
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Updated {updated_count} ideas with rich content")
    print(f"⚠️  Failed: {failed_count} ideas")
    print(f"📊 Total with rich content: {ideas_already_done + updated_count}/{len(ideas)}")
    print("=" * 70)
    
    if failed_count > 0:
        print("\n💡 TIP: If API credits ran out, add more at:")
        print("   https://openrouter.ai/settings/credits")
        print("   Then run this script again to continue.")
    
    if updated_count == len(ideas_to_update):
        print("\n🎉 SUCCESS! All ideas now have rich content!")
        print("   Refresh your browser to see the changes.")


if __name__ == "__main__":
    main()
