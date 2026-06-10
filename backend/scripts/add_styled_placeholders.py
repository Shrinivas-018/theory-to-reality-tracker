"""
Add Styled Placeholder Images

Adds professional-looking colored placeholders for each Yuga stage.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.mongodb_service import MongoDBService


def add_styled_images():
    """Add styled placeholder images with Yuga-themed colors."""
    mongo = MongoDBService()
    
    print("=" * 70)
    print("🎨 ADDING STYLED YUGA IMAGES")
    print("=" * 70)
    
    # Get all ideas
    ideas = mongo.get_all_ideas(limit=1000)
    print(f"\n📊 Found {len(ideas)} ideas to update")
    
    # Yuga color schemes (background/text)
    yuga_styles = {
        "satya_yuga": {
            "bg": "FFD700",  # Gold
            "text": "8B4513",  # Brown
            "name": "Satya Yuga (Golden Age)"
        },
        "treta_yuga": {
            "bg": "C0C0C0",  # Silver
            "text": "2F4F4F",  # Dark slate
            "name": "Treta Yuga (Silver Age)"
        },
        "dwapar_yuga": {
            "bg": "CD7F32",  # Bronze
            "text": "FFFFFF",  # White
            "name": "Dwapar Yuga (Bronze Age)"
        },
        "kali_yuga": {
            "bg": "4B0082",  # Indigo
            "text": "FFD700",  # Gold
            "name": "Kali Yuga (Iron Age)"
        }
    }
    
    updated_count = 0
    
    for i, idea in enumerate(ideas, 1):
        idea_name = idea.get("idea", "")
        print(f"[{i}/{len(ideas)}] {idea_name}")
        
        # Update images for each Yuga
        for yuga_stage in ["satya_yuga", "treta_yuga", "dwapar_yuga", "kali_yuga"]:
            if yuga_stage in idea.get("evolution", {}):
                style = yuga_styles[yuga_stage]
                
                # Create styled placeholder URL using placehold.co (more reliable)
                text = idea_name.replace(" ", "%20")
                image_url = f"https://placehold.co/800x600/{style['bg']}/{style['text']}?text={text}"
                
                idea["evolution"][yuga_stage]["image"] = {
                    "url": image_url,
                    "alt": f"{idea_name} in {yuga_stage.replace('_', ' ').title()}",
                    "source": style['name'],
                    "styled": True
                }
        
        # Update in database
        if mongo.is_connected():
            try:
                mongo.collection.update_one(
                    {"idea": idea_name},
                    {"$set": {"evolution": idea["evolution"]}}
                )
                updated_count += 1
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Updated {updated_count} ideas with styled images")
    print("=" * 70)


if __name__ == "__main__":
    add_styled_images()
