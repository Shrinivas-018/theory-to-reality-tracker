"""
Cleanup Nonsense Ideas

Removes software/programming ideas that don't make sense in ancient Yugas.
Keeps only physical inventions and scientific concepts.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.mongodb_service import MongoDBService


def cleanup_ideas():
    """Remove software/programming ideas that don't fit Yuga evolution."""
    mongo = MongoDBService()
    
    print("=" * 70)
    print("🧹 CLEANING UP NONSENSE IDEAS")
    print("=" * 70)
    
    # Ideas to remove - software, programming, GitHub repos, etc.
    nonsense_ideas = [
        # Programming languages & frameworks
        "Python", "Python-100-Days", "react", "vue", "tensorflow", "linux",
        "javascript-algorithms", "computer-science",
        
        # GitHub repositories
        "AutoGPT", "CS-Notes", "You-Dont-Know-JS", "vscode", "n8n", "ohmyzsh",
        "claw-code", "openclaw", "superpowers", "awesome", "build-your-own-x",
        "freeCodeCamp", "public-apis", "free-programming-books",
        "awesome-selfhosted", "awesome-python", "coding-interview-university",
        "system-design-primer", "developer-roadmap", "project-based-learning",
        "996.ICU", "the-book-of-secret-knowledge",
        
        # Modern software concepts
        "Cloud Computing", "Edge Computing", "Blockchain", "Cryptocurrency",
        "Smart Contracts", "E-commerce", "Video Streaming", "Cloud Storage",
        "Mobile Apps", "Search Engine", "Web Browser", "Operating System",
        "Digital Payment", "GPS Navigation", "Social Media", "Email",
        "World Wide Web", "Internet", "Video Conferencing",
        
        # Modern tech that's too abstract
        "IoT Devices", "5G Technology", "WiFi", "Bluetooth", "Fiber Optics",
        "Satellite Communication", "Augmented Reality", "Virtual Reality",
        "Smartwatch", "Tablet", "Laptop", "Personal Computer", "Smartphone",
        
        # AI/ML concepts
        "Artificial Intelligence", "Machine Learning", "Deep Learning",
        "Neural Networks", "Computer Vision", "Natural Language Processing",
        
        # Modern devices
        "3D Printing", "Drones", "Robots", "drone", "weapons"
    ]
    
    # Get all ideas
    all_ideas = mongo.get_all_ideas(limit=1000)
    print(f"\n📊 Total ideas before cleanup: {len(all_ideas)}")
    
    removed_count = 0
    
    for idea_name in nonsense_ideas:
        if mongo.is_connected():
            try:
                result = mongo.collection.delete_one({"idea": idea_name})
                if result.deleted_count > 0:
                    print(f"  ✓ Removed: {idea_name}")
                    removed_count += 1
            except Exception as e:
                print(f"  ✗ Error removing {idea_name}: {e}")
    
    # Get updated count
    remaining_ideas = mongo.get_all_ideas(limit=1000)
    
    print("\n" + "=" * 70)
    print(f"✅ CLEANUP COMPLETE")
    print("=" * 70)
    print(f"Removed: {removed_count} ideas")
    print(f"Remaining: {len(remaining_ideas)} ideas")
    print("\n📋 Remaining ideas are physical inventions and scientific concepts")
    print("   that make sense across all Yugas!")
    print("=" * 70)


if __name__ == "__main__":
    cleanup_ideas()
