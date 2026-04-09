"""Second pass: assign remaining General Science ideas based on broader title matching."""
import json

# Map remaining titles to categories more aggressively
TITLE_CATEGORY_MAP = {
    # Physics-related
    "work (physics)": "Classical Physics", "force": "Classical Physics", "energy": "Classical Physics",
    "mass": "Classical Physics", "velocity": "Classical Physics", "acceleration": "Classical Physics",
    "momentum": "Classical Physics", "pressure": "Classical Physics", "temperature": "Classical Physics",
    "entropy": "Classical Physics", "wave": "Classical Physics", "frequency": "Classical Physics",
    "wavelength": "Classical Physics", "radiation": "Nuclear Physics", "photon": "Quantum Physics",
    "electron": "Quantum Physics", "ion": "Chemistry", "atom": "Nuclear Physics",
    "magnetism": "Classical Physics", "gravity": "Classical Physics", "relativity": "Classical Physics",
    "electromagnetic": "Classical Physics", "light": "Classical Physics", "sound": "Classical Physics",
    "density": "Classical Physics", "voltage": "Engineering", "current": "Engineering",
    "resistance": "Engineering", "power": "Engineering", "heat": "Classical Physics",
    
    # Bio/Med
    "cell": "Biology", "virus": "Biology", "bacteria": "Biology", "dna": "Biology",
    "protein": "Biology", "tissue": "Biology", "organ": "Biology", "blood": "Medicine",
    "muscle": "Medicine", "bone": "Medicine", "lung": "Medicine", "heart": "Medicine",
    "kidney": "Medicine", "liver": "Medicine", "skin": "Medicine", "tooth": "Medicine",
    "infection": "Medicine", "cancer": "Medicine", "tumor": "Medicine", "fever": "Medicine",
    "pain": "Medicine", "inflammation": "Medicine", "allergy": "Medicine", "asthma": "Medicine",
    "diabetes": "Medicine", "obesity": "Medicine", "stroke": "Medicine", "epilepsy": "Medicine",
    "hyporeflexia": "Medicine", "sleep": "Neuroscience", "memory": "Neuroscience",
    "perception": "Neuroscience", "cognition": "Neuroscience", "emotion": "Neuroscience",
    "anxiety": "Neuroscience", "depression": "Neuroscience",
    
    # Social Sciences
    "psychology": "Neuroscience", "social psychology": "Neuroscience",
    "sociology": "Philosophy", "anthropology": "Philosophy", "history": "Philosophy",
    "education": "Philosophy", "language": "Philosophy", "linguistics": "Philosophy",
    "law": "Political Science", "justice": "Political Science", "government": "Political Science",
    "war": "Political Science", "peace": "Political Science", "religion": "Philosophy",
    
    # Earth/Geo
    "ocean": "Earth Science", "river": "Earth Science", "mountain": "Earth Science",
    "volcano": "Earth Science", "earthquake": "Earth Science", "soil": "Earth Science",
    "weather": "Earth Science", "cloud": "Earth Science", "rain": "Earth Science",
    "wind": "Earth Science", "physical geography": "Earth Science", "map": "Earth Science",
    "continent": "Earth Science", "island": "Earth Science",
    
    # Tech
    "internet": "Information Science", "web": "Information Science", "computer": "Computer Science",
    "software": "Computer Science", "hardware": "Computer Science", "robot": "Engineering",
    "laser": "Engineering", "radar": "Engineering", "satellite": "Engineering",
    "telescope": "Astrophysics", "microscope": "Biology",
    
    # Chem/Materials  
    "metal": "Materials Science", "plastic": "Materials Science", "glass": "Materials Science",
    "water": "Chemistry", "acid": "Chemistry", "base": "Chemistry", "salt": "Chemistry",
    "gas": "Chemistry", "liquid": "Chemistry", "solid": "Chemistry",
    "oxygen": "Chemistry", "hydrogen": "Chemistry", "carbon": "Chemistry", "nitrogen": "Chemistry",
    
    # Astro
    "planet": "Astrophysics", "moon": "Astrophysics", "sun": "Astrophysics",
    "comet": "Astrophysics", "asteroid": "Astrophysics", "meteor": "Astrophysics",
    "universe": "Astrophysics", "cosmos": "Astrophysics", "space": "Astrophysics",
}

def main():
    path = "data/evolution_tracker_api/ideas.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for idea_id, idea in data.items():
        if idea["category"] != "General Science":
            continue
        
        title_lower = idea["title"].lower().strip()
        
        # Direct title match
        if title_lower in TITLE_CATEGORY_MAP:
            idea["category"] = TITLE_CATEGORY_MAP[title_lower]
            changed += 1
            continue
        
        # Partial match on keywords
        all_kw = " ".join(idea.get("keywords", [])).lower()
        matched = False
        for pattern, cat in TITLE_CATEGORY_MAP.items():
            if pattern in title_lower or pattern in all_kw:
                idea["category"] = cat
                changed += 1
                matched = True
                break
        
        # If still no match, assign based on first keyword
        if not matched and idea.get("keywords"):
            kw = idea["keywords"][0].lower()
            if kw in TITLE_CATEGORY_MAP:
                idea["category"] = TITLE_CATEGORY_MAP[kw]
                changed += 1

    # Count final distribution
    cat_counts = {}
    for idea in data.values():
        cat_counts[idea["category"]] = cat_counts.get(idea["category"], 0) + 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Second pass: re-categorized {changed} more ideas")
    print(f"\nFinal Distribution ({len(cat_counts)} categories):")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    remaining = cat_counts.get("General Science", 0)
    print(f"\nRemaining General Science: {remaining}")

if __name__ == "__main__":
    main()
