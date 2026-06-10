from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ─── MongoDB connection ─────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_mongo_client = None
_laureates_collection = None
_mongo_connected = False

# Sample data (used for initial seeding)
SAMPLE_LAUREATES = [
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


def _init_mongo():
    """Initialize MongoDB connection and seed laureates if needed."""
    global _mongo_client, _laureates_collection, _mongo_connected
    
    try:
        from pymongo import MongoClient
    except ImportError:
        print("[WARN] pymongo not installed — laureates using in-memory data.")
        return
    
    uri = os.getenv("MONGODB_ATLAS_URI", os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
    db_name = os.getenv("MONGODB_DATABASE", "yuga_evolution_db")
    is_atlas = "mongodb+srv://" in uri
    
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
    
    try:
        import time
        client = MongoClient(uri, **params)
        for attempt in range(3):
            try:
                client.server_info()
                break
            except Exception:
                if attempt < 2:
                    time.sleep(2)
                else:
                    raise
        
        _mongo_client = client
        db = client[db_name]
        _laureates_collection = db["laureates"]
        _mongo_connected = True
        
        # Create index
        _laureates_collection.create_index([("laureate", 1), ("year", 1)])
        
        # Seed if empty
        if _laureates_collection.count_documents({}) == 0:
            _laureates_collection.insert_many(SAMPLE_LAUREATES)
            print(f"[OK] Seeded {len(SAMPLE_LAUREATES)} laureates into MongoDB")
        
        conn_type = "MongoDB Atlas" if is_atlas else "Local MongoDB"
        print(f"[OK] Laureates API connected to {conn_type}: {db_name}.laureates")
    except Exception as e:
        print(f"[WARN] Laureates MongoDB connection failed: {e}")
        print("  Using in-memory data for laureates.")
        _mongo_connected = False


def _get_all_laureates():
    """Get all laureates from MongoDB or in-memory fallback."""
    if _mongo_connected and _laureates_collection is not None:
        try:
            docs = list(_laureates_collection.find({}, {"_id": 0}))
            if docs:
                return docs
        except Exception as e:
            print(f"[WARN] MongoDB read failed: {e}")
    return SAMPLE_LAUREATES


# Initialize on module load
_init_mongo()


@app.route("/")
def home():
    return jsonify({
        "message": "Nobel API running",
        "storage": "MongoDB" if _mongo_connected else "In-memory",
        "endpoints": ["/laureates", "/search?name=Einstein", "/categories", "/stats", "/connections"]
    })

@app.route("/laureates")
def laureates():
    category = request.args.get("category", "")
    all_data = _get_all_laureates()
    if category:
        result = [r for r in all_data if r.get("category") == category]
    else:
        result = all_data
    return jsonify(result)

@app.route("/search")
def search():
    name = request.args.get("name", "")
    all_data = _get_all_laureates()
    results = [r for r in all_data if name.lower() in r.get("laureate", "").lower()]
    return jsonify(results)

@app.route("/categories")
def categories():
    all_data = _get_all_laureates()
    cats = list(set(r.get("category", "") for r in all_data))
    return jsonify(cats)

@app.route("/stats")
def stats():
    all_data = _get_all_laureates()
    years = [r["year"] for r in all_data if "year" in r]
    cats = set(r.get("category", "") for r in all_data)
    return jsonify({
        "total_laureates": len(all_data),
        "categories": len(cats),
        "earliest_year": min(years) if years else None,
        "latest_year": max(years) if years else None,
        "storage": "MongoDB" if _mongo_connected else "In-memory"
    })

@app.route("/connections")
def connections():
    import networkx as nx
    all_data = _get_all_laureates()
    G = nx.Graph()
    for row in all_data:
        G.add_node(row["laureate"], year=row["year"], category=row["category"])
    
    # Group by year and category
    from collections import defaultdict
    groups = defaultdict(list)
    for row in all_data:
        groups[(row["year"], row["category"])].append(row["laureate"])
    
    for _, names in groups.items():
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                G.add_edge(names[i], names[j])
    
    nodes = [{"id": n, "label": n} for n in G.nodes()]
    edges = [{"source": e[0], "target": e[1]} for e in G.edges()]
    return jsonify({"nodes": nodes, "edges": edges})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
