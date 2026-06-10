"""
One-time migration script to import all existing JSON data into MongoDB.

Run this script to populate MongoDB Atlas with data from:
1. data/evolution_tracker_api/ideas.json  →  evolution_ideas collection
2. data/evolution_tracker_api/edges.json  →  evolution_edges collection
3. data/yuga_evolution_fallback/ideas.json → ideas collection
4. Sample laureate data                   → laureates collection

Usage:
    python migrate_to_mongodb.py
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_mongo_client():
    """Create and test a MongoDB connection."""
    try:
        from pymongo import MongoClient
    except ImportError:
        print("❌ pymongo not installed. Run: pip install pymongo")
        sys.exit(1)
    
    uri = os.getenv(
        "MONGODB_ATLAS_URI",
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    )
    db_name = os.getenv("MONGODB_DATABASE", "yuga_evolution_db")
    is_atlas = "mongodb+srv://" in uri
    
    print(f"📡 Connecting to {'MongoDB Atlas' if is_atlas else 'Local MongoDB'}...")
    print(f"   Database: {db_name}")
    
    timeout = 30000 if is_atlas else 5000
    params = {
        "serverSelectionTimeoutMS": timeout,
        "connectTimeoutMS": timeout,
        "retryWrites": True,
        "maxPoolSize": 50,
        "minPoolSize": 10,
    }
    if is_atlas:
        params["ssl"] = True
        params["tlsInsecure"] = True
    
    client = MongoClient(uri, **params)
    
    # Test connection
    for attempt in range(3):
        try:
            info = client.server_info()
            print(f"✅ Connected! Server version: {info.get('version', 'unknown')}")
            break
        except Exception as e:
            if attempt < 2:
                print(f"   Attempt {attempt + 1} failed, retrying in 2s...")
                time.sleep(2)
            else:
                print(f"❌ Connection failed: {e}")
                sys.exit(1)
    
    return client, db_name


def migrate_evolution_ideas(db):
    """Migrate evolution tracker ideas from JSON to MongoDB."""
    ideas_file = Path(BASE_DIR) / "data" / "evolution_tracker_api" / "ideas.json"
    collection = db["evolution_ideas"]
    
    if not ideas_file.exists():
        print(f"\n⚠️  {ideas_file} not found — skipping evolution ideas")
        return 0
    
    with open(ideas_file, 'r', encoding='utf-8') as f:
        ideas_data = json.load(f)
    
    total = len(ideas_data)
    print(f"\n📦 Migrating {total} evolution ideas...")
    
    inserted = 0
    updated = 0
    errors = 0
    
    for idea_id, idea_dict in ideas_data.items():
        idea_dict["id"] = idea_id
        try:
            result = collection.replace_one(
                {"id": idea_id},
                idea_dict,
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"   Error: {e}")
    
    # Create indexes
    collection.create_index("id", unique=True)
    collection.create_index("category")
    collection.create_index("stage")
    
    print(f"   ✅ Inserted: {inserted}, Updated: {updated}, Errors: {errors}")
    return inserted + updated


def migrate_evolution_edges(db):
    """Migrate evolution tracker edges from JSON to MongoDB."""
    edges_file = Path(BASE_DIR) / "data" / "evolution_tracker_api" / "edges.json"
    collection = db["evolution_edges"]
    
    if not edges_file.exists():
        print(f"\n⚠️  {edges_file} not found — skipping evolution edges")
        return 0
    
    with open(edges_file, 'r', encoding='utf-8') as f:
        edges_data = json.load(f)
    
    total = len(edges_data)
    print(f"\n📦 Migrating {total} evolution edges...")
    
    # Clear existing and re-insert (edges don't have unique IDs)
    collection.delete_many({})
    
    if edges_data:
        try:
            result = collection.insert_many(edges_data, ordered=False)
            count = len(result.inserted_ids)
            print(f"   ✅ Inserted: {count}")
        except Exception as e:
            print(f"   ⚠️  Partial insert: {e}")
            count = collection.count_documents({})
            print(f"   ✅ Total in collection: {count}")
    
    # Create index
    collection.create_index([("source_id", 1), ("target_id", 1)])
    
    return collection.count_documents({})


def migrate_yuga_ideas(db):
    """Migrate Yuga evolution ideas from JSON fallback to MongoDB."""
    fallback_file = Path(BASE_DIR) / "data" / "yuga_evolution_fallback" / "ideas.json"
    collection = db["ideas"]  # Uses the MONGODB_COLLECTION env var default
    
    if not fallback_file.exists():
        print(f"\n⚠️  {fallback_file} not found — skipping yuga ideas")
        return 0
    
    with open(fallback_file, 'r', encoding='utf-8') as f:
        yuga_data = json.load(f)
    
    total = len(yuga_data)
    print(f"\n📦 Migrating {total} Yuga evolution ideas...")
    
    inserted = 0
    updated = 0
    errors = 0
    
    for record in yuga_data:
        idea_name = record.get("idea", "")
        if not idea_name:
            errors += 1
            continue
        try:
            result = collection.replace_one(
                {"idea": idea_name},
                record,
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"   Error: {e}")
    
    # Create indexes
    collection.create_index("idea", unique=True)
    collection.create_index("timestamp")
    
    print(f"   ✅ Inserted: {inserted}, Updated: {updated}, Errors: {errors}")
    return inserted + updated


def migrate_laureates(db):
    """Seed Nobel laureates into MongoDB."""
    collection = db["laureates"]
    
    laureates = [
        {"laureate": "Albert Einstein", "category": "Physics", "year": 1921, "motivation": "Discovery of the photoelectric effect"},
        {"laureate": "Marie Curie", "category": "Physics", "year": 1903, "motivation": "Research on radiation phenomena"},
        {"laureate": "Marie Curie", "category": "Chemistry", "year": 1911, "motivation": "Discovery of radium and polonium"},
        {"laureate": "Richard Feynman", "category": "Physics", "year": 1965, "motivation": "Fundamental work in quantum electrodynamics"},
        {"laureate": "Werner Heisenberg", "category": "Physics", "year": 1932, "motivation": "Creation of quantum mechanics"},
        {"laureate": "Niels Bohr", "category": "Physics", "year": 1922, "motivation": "Investigation of atomic structure"},
        {"laureate": "Ernest Rutherford", "category": "Chemistry", "year": 1908, "motivation": "Investigations into disintegration of elements"},
        {"laureate": "Linus Pauling", "category": "Chemistry", "year": 1954, "motivation": "Research into chemical bonds"},
        {"laureate": "Alexander Fleming", "category": "Medicine", "year": 1945, "motivation": "Discovery of penicillin"},
        {"laureate": "Francis Crick", "category": "Medicine", "year": 1962, "motivation": "Discoveries concerning molecular structure of DNA"},
        {"laureate": "James Watson", "category": "Medicine", "year": 1962, "motivation": "Discoveries concerning molecular structure of DNA"},
        {"laureate": "Ivan Pavlov", "category": "Medicine", "year": 1904, "motivation": "Work on physiology of digestion"},
        {"laureate": "Martin Luther King Jr.", "category": "Peace", "year": 1964, "motivation": "Non-violent struggle for civil rights"},
        {"laureate": "Malala Yousafzai", "category": "Peace", "year": 2014, "motivation": "Struggle against suppression of children and for right to education"},
        {"laureate": "Paul Samuelson", "category": "Economics", "year": 1970, "motivation": "Scientific work developing static and dynamic economic theory"},
        {"laureate": "Milton Friedman", "category": "Economics", "year": 1976, "motivation": "Achievements in consumption analysis and monetary history"},
    ]
    
    existing = collection.count_documents({})
    if existing > 0:
        print(f"\n📦 Laureates collection already has {existing} records — skipping seed")
        return existing
    
    print(f"\n📦 Seeding {len(laureates)} laureates...")
    
    collection.insert_many(laureates)
    collection.create_index([("laureate", 1), ("year", 1)])
    
    print(f"   ✅ Inserted: {len(laureates)}")
    return len(laureates)


def verify_migration(db):
    """Verify all collections have data."""
    print("\n" + "=" * 50)
    print("📊 MIGRATION VERIFICATION")
    print("=" * 50)
    
    collections = {
        "evolution_ideas": "Evolution Tracker Ideas",
        "evolution_edges": "Evolution Tracker Edges",
        "ideas": "Yuga Evolution Ideas",
        "laureates": "Nobel Laureates",
    }
    
    all_ok = True
    for coll_name, label in collections.items():
        count = db[coll_name].count_documents({})
        status = "✅" if count > 0 else "❌"
        if count == 0:
            all_ok = False
        print(f"   {status} {label} ({coll_name}): {count} documents")
    
    print()
    if all_ok:
        print("🎉 ALL DATA SUCCESSFULLY MIGRATED TO MONGODB!")
    else:
        print("⚠️  Some collections are empty — check the warnings above.")
    
    return all_ok


def main():
    print("=" * 50)
    print("🚀 MongoDB Migration Script")
    print("=" * 50)
    
    client, db_name = get_mongo_client()
    db = client[db_name]
    
    # Migrate all data sources
    migrate_evolution_ideas(db)
    migrate_evolution_edges(db)
    migrate_yuga_ideas(db)
    migrate_laureates(db)
    
    # Verify
    verify_migration(db)
    
    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
