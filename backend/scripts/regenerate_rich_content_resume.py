"""
Regenerate Rich Content for Yugas (Resume Version)

This version can resume from where it left off and handles API errors gracefully.
It skips ideas that already have rich content (time_period field exists).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.mongodb_service import MongoDBService
from backend.services.yuga_generator import YugaGeneratorService
import time


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
    
    # Time periods for each Yuga
    time_periods = {
        "satya_yuga": "10,000 BCE - 5,000 BCE",
        "treta_yuga": "5,000 BCE - 1,000 BCE",
        "dwapar_yuga": "1,000 BCE - 1500 CE",
        "kali_yuga": "1500 CE - Present"
    }
    
    yuga_gen = YugaGeneratorService()
    
    # Generate base evolution
    try:
        evolution = yuga_gen.generate_yuga_evolution(idea_name, description)
    except Exception as e:
        print(f"  ✗ API Error: {e}")
        return None
    
    # Enhance each Yuga with richer content
    for yuga in ["satya_yuga", "treta_yuga", "dwapar_yuga", "kali_yuga"]:
        if yuga in evolution:
            # Add time period
            evolution[yuga]["time_period"] = time_periods[yuga]
            
            # Enhance description (make it longer and more detailed)
            original_desc = evolution[yuga].get("description", "")
            evolution[yuga]["description"] = f"{original_desc}\n\nThis manifestation represented a fundamental shift in how humanity interacted with the concept of {idea_name}. The methods, materials, and philosophical understanding of this innovation were deeply intertwined with the spiritual and technological consciousness of the era. People's relationship with {idea_name} was not merely functional but carried profound symbolic and cultural significance that shaped their daily lives and worldview."
            
            # Convert characteristics to point-wise list
            chars = evolution[yuga].get("characteristics", "")
            if chars:
                char_points = [c.strip() for c in chars.split(",")]
                evolution[yuga]["characteristics_list"] = char_points
            
            # Add detailed statistics with numbers
            stats = evolution[yuga].get("statistics", "")
            evolution[yuga]["statistics_detailed"] = {
                "original": stats,
                "metrics": extract_metrics(stats, yuga)
            }
    
    return evolution


def extract_metrics(stats_text: str, yuga: str) -> list:
    """Extract and enhance metrics from statistics text."""
    metrics = []
    
    # Parse existing stats
    if "efficiency" in stats_text.lower():
        if "100%" in stats_text or "divine" in stats_text:
            metrics.append({"label": "Efficiency", "value": "100%", "icon": "✓"})
        elif "75%" in stats_text:
            metrics.append({"label": "Efficiency", "value": "75%", "icon": "⚡"})
        elif "50%" in stats_text:
            metrics.append({"label": "Efficiency", "value": "50%", "icon": "⚙️"})
        else:
            metrics.append({"label": "Efficiency", "value": "Variable", "icon": "📊"})
    
    # Add time-based metrics
    if yuga == "satya_yuga":
        metrics.extend([
            {"label": "Speed", "value": "Instantaneous", "icon": "⚡"},
            {"label": "Energy", "value": "Divine/Natural", "icon": "🌟"},
            {"label": "Accessibility", "value": "Universal", "icon": "🌍"}
        ])
    elif yuga == "treta_yuga":
        metrics.extend([
            {"label": "Speed", "value": "Hours", "icon": "⏰"},
            {"label": "Energy", "value": "Ritual/Manual", "icon": "🔥"},
            {"label": "Accessibility", "value": "Priests/Sages", "icon": "👥"}
        ])
    elif yuga == "dwapar_yuga":
        metrics.extend([
            {"label": "Speed", "value": "Minutes-Hours", "icon": "⏱️"},
            {"label": "Energy", "value": "Mechanical", "icon": "⚙️"},
            {"label": "Accessibility", "value": "Craftsmen", "icon": "🔨"}
        ])
    else:  # kali_yuga
        metrics.extend([
            {"label": "Speed", "value": "Seconds-Minutes", "icon": "⚡"},
            {"label": "Energy", "value": "Electrical", "icon": "🔌"},
            {"label": "Accessibility", "value": "Mass Market", "icon": "🏪"}
        ])
    
    return metrics


def main():
    """Regenerate ideas that don't have rich content yet."""
    mongo = MongoDBService()
    
    print("=" * 70)
    print("🔄 REGENERATING WITH RICH CONTENT (RESUME MODE)")
    print("=" * 70)
    
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
    
    print("\n⏱️  This will take some time...\n")
    
    updated_count = 0
    failed_count = 0
    
    for i, idea in enumerate(ideas_to_update, 1):
        idea_name = idea.get("idea", "")
        description = idea.get("description", "")
        
        print(f"[{i}/{len(ideas_to_update)}] Regenerating: {idea_name}")
        
        try:
            # Generate rich evolution
            rich_evolution = generate_rich_evolution(idea_name, description)
            
            if rich_evolution is None:
                print(f"  ⚠️  Skipped due to API error")
                failed_count += 1
                continue
            
            # Update in database
            if mongo.is_connected():
                mongo.collection.update_one(
                    {"idea": idea_name},
                    {"$set": {"evolution": rich_evolution}}
                )
                updated_count += 1
                print(f"  ✓ Updated with rich content")
            
            # Rate limiting
            time.sleep(1)
            
            # Pause every 10 ideas
            if i % 10 == 0:
                print(f"\n  ⏸️  Pausing 5 seconds...")
                time.sleep(5)
                
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


if __name__ == "__main__":
    main()
