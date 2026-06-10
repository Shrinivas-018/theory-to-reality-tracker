"""
Regenerate Rich Content for Yugas

Creates detailed, lengthy content for each Yuga with:
- Longer descriptions (200+ words)
- Detailed statistics with numbers
- Point-wise characteristics
- Time periods
- Societal impact details
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.mongodb_service import MongoDBService
from backend.services.yuga_generator import YugaGeneratorService
import time


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
    evolution = yuga_gen.generate_yuga_evolution(idea_name, description)
    
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
    """Regenerate all ideas with rich content."""
    mongo = MongoDBService()
    
    print("=" * 70)
    print("🔄 REGENERATING WITH RICH CONTENT")
    print("=" * 70)
    
    # Get all ideas
    ideas = mongo.get_all_ideas(limit=1000)
    print(f"\n📊 Found {len(ideas)} ideas to regenerate")
    print("⏱️  This will take some time...\n")
    
    updated_count = 0
    
    for i, idea in enumerate(ideas, 1):
        idea_name = idea.get("idea", "")
        description = idea.get("description", "")
        
        print(f"[{i}/{len(ideas)}] Regenerating: {idea_name}")
        
        try:
            # Generate rich evolution
            rich_evolution = generate_rich_evolution(idea_name, description)
            
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
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Updated {updated_count} ideas with rich content")
    print("=" * 70)


if __name__ == "__main__":
    main()
