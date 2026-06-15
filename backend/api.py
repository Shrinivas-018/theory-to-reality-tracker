"""
Enhanced Flask API for the Theory-to-Reality Evolution Tracker.

Provides RESTful endpoints for ideas, temporal queries, lineage graph,
AI predictions, dataset export, and dashboard statistics.
Seeds 3 evolution chains on startup.
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from pathlib import Path

# Load .env file if present
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore, LineageGraph, AIPredictionService, DatasetExporter, NLPExtractorService, LLMSummarizerService
from backend.services.mongodb_service import MongoDBService
from backend.services.yuga_generator import YugaGeneratorService
from backend.services.yuga_data_structures import YugaDataStructures
from backend.data_structures import IntervalTree, SegmentTree

import json
import re
import requests

app = Flask(__name__)
CORS(app)

from backend.services.auth_service import hash_password, verify_password

# ─── Shared state ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "evolution_tracker_api")

class UserContext:
    def __init__(self, user_id: str):
        self.user_id = user_id
        # Isolate DataStore per user
        self.store = DataStore(data_dir=DATA_DIR, user_id=user_id if user_id != "default" else None)
        self.interval_tree = IntervalTree()
        self.segment_tree = SegmentTree(min_year=1800, max_year=2200)
        self.lineage_graph = LineageGraph()
        
        # Services mapping to this user's isolated data
        self.prediction_service = AIPredictionService(self.store, self.lineage_graph)
        self.dataset_exporter = DatasetExporter(self.store, self.lineage_graph)
        self.nlp_service = NLPExtractorService(self.store)
        self.llm_service = LLMSummarizerService(self.store)
        
        self.yuga_ds = YugaDataStructures()
        self.yuga_loaded = False
        
        self._seed_data()
        
    def _seed_data(self):
        """Seed this user's context memory structures from their isolated DataStore."""
        ideas = self.store.get_all_ideas()
        edges = self.store.get_all_edges()
        
        for idea in ideas:
            try:
                self.lineage_graph.add_idea(idea)
            except ValueError:
                pass
            s = idea.start_year
            e = idea.end_year or s
            self.interval_tree.insert(s, e, idea.id)
            self.segment_tree.update(s, e)
            
        for edge in edges:
            try:
                self.lineage_graph.add_influence(edge)
            except ValueError:
                pass
                
    def load_yuga_structures(self, mongo_service: MongoDBService):
        """Load Yuga structures lazily once when needed."""
        if self.yuga_loaded:
            return
        try:
            ideas = mongo_service.get_all_ideas(limit=1000, user_id=self.user_id if self.user_id != "default" else None)
            if ideas:
                self.yuga_ds.load_ideas(ideas)
                self.yuga_loaded = True
        except Exception as e:
            print(f"[WARN] Failed to load Yuga structures for user {self.user_id}: {e}")

_contexts = {}

def get_user_context(user_id: str = None) -> UserContext:
    if not user_id:
        user_id = "default"
    if user_id not in _contexts:
        _contexts[user_id] = UserContext(user_id)
    return _contexts[user_id]

class ContextProxy:
    def __init__(self, attribute_name):
        object.__setattr__(self, "_attr", attribute_name)
        
    def _get_target(self):
        from flask import g
        try:
            ctx = getattr(g, "context", None)
            if ctx is None:
                ctx = get_user_context("default")
            return getattr(ctx, object.__getattribute__(self, "_attr"))
        except RuntimeError:
            return getattr(get_user_context("default"), object.__getattribute__(self, "_attr"))
            
    def __getattr__(self, name):
        return getattr(self._get_target(), name)
        
    def __setattr__(self, name, value):
        setattr(self._get_target(), name, value)
        
    def __getitem__(self, key):
        return self._get_target()[key]
        
    def __setitem__(self, key, value):
        self._get_target()[key] = value
        
    def __len__(self):
        return len(self._get_target())

    def __iter__(self):
        return iter(self._get_target())
        
    def __bool__(self):
        return bool(self._get_target())

# Proxy global references
store = ContextProxy("store")
interval_tree = ContextProxy("interval_tree")
segment_tree = ContextProxy("segment_tree")
lineage_graph = ContextProxy("lineage_graph")
prediction_service = ContextProxy("prediction_service")
dataset_exporter = ContextProxy("dataset_exporter")
nlp_service = ContextProxy("nlp_service")
llm_service = ContextProxy("llm_service")
yuga_ds = ContextProxy("yuga_ds")

# ─── Yugas Services ──────────────────────────────────────────────
mongo_service = MongoDBService()
yuga_generator = YugaGeneratorService()



# ─── Helpers ─────────────────────────────────────────────────────

def ok_response(data, message="success"):
    """Standardised success envelope."""
    return jsonify({"status": "success", "message": message, "data": data})


def error_response(message, status_code=400):
    """Standardised error envelope."""
    return jsonify({"status": "error", "message": message}), status_code


def paginate(items, page=1, limit=50):
    """
    Paginate a list of items.

    Returns (page_items, pagination_meta).
    """
    total = len(items)
    start = (page - 1) * limit
    end = start + limit
    page_items = items[start:end]
    return page_items, {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": max(1, -(-total // limit)),  # ceil division
    }


def _create_evolutionary_edges_for_new_idea(idea):
    """Automatically create evolutionary edges connecting a new idea to existing available ideas."""
    try:
        # Use prediction_service to find top similar ideas
        sims = prediction_service.get_similar_ideas(idea.id, top_n=4)
        for sim in sims:
            target_idea = store.get_idea(sim["id"])
            if not target_idea:
                continue

            # Decide direction based on timeline progression
            if target_idea.start_year <= idea.start_year:
                src_id = target_idea.id
                tgt_id = idea.id
                inf_type = "derived_from"
            else:
                src_id = idea.id
                tgt_id = target_idea.id
                inf_type = "inspired_by"

            edge = InfluenceEdge(
                source_id=src_id,
                target_id=tgt_id,
                influence_type=inf_type,
                influence_weight=round(0.4 + sim.get("similarity", 0.5) * 0.5, 2),
                evidence=f"Automated evolutionary edge based on semantic and keyword similarity ({sim.get('similarity', 0.5)*100:.0f}% overlap).",
                confidence_score=round(sim.get("similarity", 0.5), 2)
            )
            store.add_edge(edge)
            try:
                lineage_graph.add_influence(edge)
            except ValueError:
                pass
    except Exception as e:
        print(f"[WARN] Failed to create evolutionary edges for new idea: {e}")


def _seed_data():
    """Load data from DataStore into in-memory temporal and graph structures."""
    ideas = store.get_all_ideas()
    edges = store.get_all_edges()

    if not ideas:
        print("[WARN] DataStore is empty. Please run 'python -m backend.scripts.fetch_openalex' to fetch the scholarly dataset.")
        return

    print(f"[INFO] Loading {len(ideas)} ideas and {len(edges)} edges from DataStore...")

    dup_ideas = 0
    for idea in ideas:
        try:
            lineage_graph.add_idea(idea)
        except ValueError:
            dup_ideas += 1  # already in graph (e.g. duplicate in file)

        s = idea.start_year
        e = idea.end_year or s
        interval_tree.insert(s, e, idea.id)
        segment_tree.update(s, e)

    edge_ok = 0
    edge_fail = 0
    for edge in edges:
        try:
            lineage_graph.add_influence(edge)
            edge_ok += 1
        except ValueError:
            edge_fail += 1  # source or target missing from graph

    print(f"[OK] Loaded {lineage_graph.node_count} nodes, {edge_ok} edges into lineage graph.")
    if edge_fail > 0:
        print(f"[WARN] Skipped {edge_fail} edges (missing source/target nodes).")
    if dup_ideas > 0:
        print(f"[WARN] Skipped {dup_ideas} duplicate idea entries.")


def initialize_yuga_data_structures():
    """Initialize Yuga data structures with ideas from MongoDB."""
    try:
        # Get all ideas from MongoDB
        ideas = mongo_service.get_all_ideas(limit=1000)
        
        if ideas:
            print(f"[INFO] Loading {len(ideas)} ideas into Yuga data structures...")
            yuga_ds.load_ideas(ideas)
            stats = yuga_ds.get_statistics()
            print(f"[OK] Yuga data structures initialized:")
            print(f"     - Interval Tree: {stats.get('interval_tree_size', 0)} intervals")
            print(f"     - Segment Tree: {stats.get('total_ideas', 0)} ideas")
            print(f"     - Lineage Graph: {stats.get('lineage_graph_nodes', 0)} nodes")
        else:
            print("[WARN] No ideas found in MongoDB. Yuga data structures will be empty.")
    except Exception as e:
        print(f"[WARN] Failed to initialize Yuga data structures: {e}")


_seed_data()

# Initialize Yuga data structures in background to avoid blocking startup
import threading

def delayed_init():
    import time
    time.sleep(2)
    try:
        initialize_yuga_data_structures()
    except Exception as e:
        print(f"⚠ Could not initialize data structures: {e}")

threading.Thread(target=delayed_init, daemon=True).start()


# ═════════════════════════════════════════════════════════════════
# API Routes
# ═════════════════════════════════════════════════════════════════

@app.before_request
def authenticate_user():
    # Bypass auth for options preflight and public paths
    if request.method == "OPTIONS":
        return
        
    public_paths = [
        "/",
        "/api/auth/login",
        "/api/auth/register",
    ]
    if request.path in public_paths:
        return
        
    # Enforce auth for all other requests
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    else:
        token = request.args.get("token")
        
    if not token:
        return error_response("Unauthorized: No token provided", 401)
        
    user = mongo_service.get_user_from_session(token)
    if not user:
        return error_response("Unauthorized: Invalid or expired token", 401)
        
    from flask import g
    g.user = user
    g.user_id = user["id"]
    g.context = get_user_context(user["id"])
    
    # NOTE: Yuga structures are loaded lazily only when Yuga endpoints are hit,
    # NOT on every single request. This avoids loading 1000 ideas from MongoDB
    # on every API call (auth, stats, chat, etc.).


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return error_response("Username and password are required")
        
    username = data["username"].strip()
    password = data["password"].strip()
    
    if len(username) < 3 or len(password) < 6:
        return error_response("Username must be at least 3 chars and password at least 6 chars")
        
    existing = mongo_service.get_user_by_username(username)
    if existing:
        return error_response("Username already exists")
        
    pwd_hash = hash_password(password)
    try:
        user = mongo_service.register_user(username, pwd_hash)
        user_id = user["id"]
        
        # Seed standard ideas/edges files
        try:
            import shutil
            default_ideas = os.path.join(DATA_DIR, "ideas.json")
            default_edges = os.path.join(DATA_DIR, "edges.json")
            
            user_ideas = os.path.join(DATA_DIR, f"ideas_{user_id}.json")
            user_edges = os.path.join(DATA_DIR, f"edges_{user_id}.json")
            
            if os.path.exists(default_ideas):
                shutil.copy(default_ideas, user_ideas)
            if os.path.exists(default_edges):
                shutil.copy(default_edges, user_edges)
        except Exception as seed_err:
            print(f"[WARN] Standard seeding failed: {seed_err}")
            
        # Seed Yuga evolution ideas
        try:
            fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
            if fallback_file.exists():
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    yuga_data = json.load(f)
                if yuga_data:
                    for record in yuga_data:
                        record_copy = dict(record)
                        record_copy.pop("_id", None)
                        mongo_service.insert_idea(record_copy, user_id=user_id)
        except Exception as yuga_err:
            print(f"[WARN] Yuga seeding failed: {yuga_err}")
            
        return ok_response({"username": username}, "Registration successful"), 201
    except Exception as exc:
        return error_response(f"Registration failed: {str(exc)}", 500)


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return error_response("Username and password are required")
        
    username = data["username"].strip()
    password = data["password"].strip()
    
    user = mongo_service.get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return error_response("Invalid username or password", 401)
        
    token = mongo_service.create_session(user["id"])
    return ok_response({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"]
        }
    }, "Login successful")


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        mongo_service.delete_session(token)
    return ok_response(None, "Logged out successfully")


@app.route("/api/auth/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return error_response("Unauthorized: No session token", 401)
        
    token = auth_header.split(" ")[1]
    user = mongo_service.get_user_from_session(token)
    if not user:
        return error_response("Unauthorized: Invalid session", 401)
        
    return ok_response({
        "id": user["id"],
        "username": user["username"]
    })


@app.route("/api/user/search-history", methods=["GET"])
def get_user_search_history():
    from flask import g
    history = mongo_service.get_search_history(g.user_id)
    return ok_response(history)


@app.route("/api/user/search-history", methods=["POST"])
def log_user_search():
    from flask import g
    data = request.get_json()
    if not data or not data.get("query"):
        return error_response("Query is required")
    query = data["query"]
    search_type = data.get("search_type", "timeline")
    results_count = data.get("results_count", 0)
    mongo_service.log_search(g.user_id, query, search_type, results_count)
    return ok_response(None, "Search logged")



@app.route("/")
def home():
    # Get MongoDB connection info
    try:
        from backend.services.mongodb_service import MongoDBService
        mongo = MongoDBService()
        db_info = mongo.get_connection_info()
    except:
        db_info = {"connected": False, "type": "Not available"}
    
    return ok_response({
        "message": "Theory-to-Reality Evolution Tracker API",
        "version": "1.0.0",
        "database": db_info,
        "endpoints": {
            "ideas": [
                "GET  /api/ideas",
                "GET  /api/ideas/<id>",
                "POST /api/ideas",
                "PUT  /api/ideas/<id>",
                "DELETE /api/ideas/<id>",
                "GET  /api/ideas/stage/<stage>",
            ],
            "temporal": [
                "GET /api/temporal/query?start=&end=",
                "GET /api/temporal/count?start=&end=",
                "GET /api/temporal/histogram?start=&end=&buckets=",
            ],
            "graph": [
                "GET /api/graph/lineage",
                "GET /api/graph/path?from=&to=",
                "GET /api/graph/centrality",
                "GET /api/ideas/<id>/ancestors",
                "GET /api/ideas/<id>/descendants",
            ],
            "predictions": [
                "GET /api/predictions/dormant",
                "GET /api/predictions/similar/<idea_id>",
                "GET /api/predictions/forecast/<idea_id>",
                "GET /api/predictions/overview",
            ],
            "export": [
                "GET /api/export/dataset?format=csv|json|graph",
            ],
            "stats": [
                "GET /api/stats",
            ],
        },
    })


# ═══ Ideas ════════════════════════════════════════════════════════

@app.route("/api/ideas")
def get_ideas():
    """Get all ideas with optional category filter and pagination."""
    category = request.args.get("category")
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 50, type=int), 400)

    ideas = store.get_all_ideas()
    if category:
        ideas = [i for i in ideas if i.category.lower() == category.lower()]

    page_items, pagination = paginate(ideas, page, limit)
    return ok_response({
        "ideas": [i.to_dict() for i in page_items],
        "pagination": pagination,
    })


@app.route("/api/ideas/<idea_id>")
def get_idea(idea_id: str):
    """Get a single idea by ID."""
    idea = store.get_idea(idea_id)
    if idea is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    return ok_response(idea.to_dict())


@app.route("/api/ideas", methods=["POST"])
def create_idea():
    """Create a new idea."""
    data = request.get_json()
    if not data:
        return error_response("Request body required")
    try:
        if isinstance(data.get("stage"), str):
            data["stage"] = EvolutionStage.from_string(data["stage"])
        idea = IdeaNode(**data)
        store.add_idea(idea)

        # Also add to in-memory data structures
        try:
            lineage_graph.add_idea(idea)
        except ValueError:
            pass  # duplicate
        s = idea.start_year
        e = idea.end_year or s
        interval_tree.insert(s, e, idea.id)
        segment_tree.update(s, e)

        # Automatically create evolutionary edges
        _create_evolutionary_edges_for_new_idea(idea)

        return ok_response(idea.to_dict(), "Idea created"), 201
    except (ValueError, TypeError) as exc:
        return error_response(str(exc))


@app.route("/api/ideas/<idea_id>", methods=["PUT"])
def update_idea(idea_id: str):
    """Update an existing idea."""
    existing = store.get_idea(idea_id)
    if existing is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    data = request.get_json()
    if not data:
        return error_response("Request body required")
    try:
        # Merge: update only provided fields
        merged = existing.to_dict()
        merged.update(data)
        merged["id"] = idea_id  # preserve ID
        if isinstance(merged.get("stage"), str):
            merged["stage"] = EvolutionStage.from_string(merged["stage"])
        else:
            merged["stage"] = existing.stage
        # Remove datetime fields so they don't break from_dict
        merged.pop("created_at", None)
        merged.pop("updated_at", None)
        updated = IdeaNode(**merged)
        updated.created_at = existing.created_at
        store.update_idea(updated)
        return ok_response(updated.to_dict(), "Idea updated")
    except (ValueError, TypeError) as exc:
        return error_response(str(exc))


@app.route("/api/ideas/<idea_id>", methods=["DELETE"])
def delete_idea(idea_id: str):
    """Delete an idea."""
    if store.get_idea(idea_id) is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    try:
        store.delete_idea(idea_id)
        return ok_response(None, "Idea deleted")
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/ideas/stage/<stage>")
def get_ideas_by_stage(stage: str):
    """Get all ideas at a specific evolution stage."""
    try:
        evolution_stage = EvolutionStage.from_string(stage)
    except ValueError as exc:
        return error_response(str(exc))
    ideas = store.get_ideas_by_stage(evolution_stage)
    return ok_response([i.to_dict() for i in ideas])


# ═══ Temporal queries ════════════════════════════════════════════

@app.route("/api/temporal/query")
def temporal_query():
    """Find ideas active during a time period (interval tree)."""
    start = request.args.get("start", type=int)
    end = request.args.get("end", type=int)
    if start is None or end is None:
        return error_response("start and end query params required")
    try:
        idea_ids = interval_tree.query(start, end)
        ideas = [store.get_idea(i).to_dict() for i in idea_ids if store.get_idea(i)]
        return ok_response({"query": {"start": start, "end": end}, "count": len(ideas), "ideas": ideas})
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/temporal/count")
def temporal_count():
    """Count ideas active during a time period (segment tree)."""
    start = request.args.get("start", type=int)
    end = request.args.get("end", type=int)
    if start is None or end is None:
        return error_response("start and end query params required")
    try:
        count = segment_tree.range_query(start, end)
        return ok_response({"query": {"start": start, "end": end}, "aggregate_count": count})
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/temporal/histogram")
def temporal_histogram():
    """Activity histogram across year buckets."""
    start = request.args.get("start", 1800, type=int)
    end = request.args.get("end", 2100, type=int)
    buckets = request.args.get("buckets", 10, type=int)
    bucket_size = max(1, (end - start) // buckets)
    histogram = []
    for b in range(buckets):
        s = start + b * bucket_size
        e = s + bucket_size - 1
        try:
            count = segment_tree.range_query(s, e)
        except Exception:
            count = 0
        histogram.append({"start": s, "end": e, "count": count})
    return ok_response(histogram)


# ═══ Graph queries ═══════════════════════════════════════════════

@app.route("/api/graph/lineage")
def get_lineage():
    """Get the full lineage graph (nodes + edges), capped at 500 nodes."""
    data = lineage_graph.to_json()
    nodes = data.get("nodes", [])[:400]
    node_ids = {n["id"] for n in nodes}
    edges = [e for e in data.get("edges", []) if e["source"] in node_ids and e["target"] in node_ids]
    return ok_response({"nodes": nodes, "edges": edges})


@app.route("/api/graph/path")
def get_path():
    """Find evolution path between two ideas."""
    src = request.args.get("from")
    tgt = request.args.get("to")
    if not src or not tgt:
        return error_response("'from' and 'to' query params required")
    try:
        path = lineage_graph.find_evolution_path(src, tgt)
        if path is None:
            return ok_response({"path": None, "message": "No path found"})
        path_ideas = [store.get_idea(i).to_dict() for i in path if store.get_idea(i)]
        return ok_response({"path": path, "path_details": path_ideas})
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/graph/centrality")
def get_centrality():
    """Get PageRank-style influence centrality for all ideas."""
    scores = lineage_graph.get_influence_centrality()
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ok_response({"centrality": [{"id": k, "score": round(v, 4)} for k, v in ranked]})


@app.route("/api/ideas/<idea_id>/ancestors")
def get_ancestors(idea_id: str):
    """Get all ancestor ideas."""
    if not lineage_graph.has_idea(idea_id):
        return error_response(f"Idea '{idea_id}' not found in graph", 404)
    try:
        ancestors = lineage_graph.get_ancestors(idea_id)
        ideas = [store.get_idea(a).to_dict() for a in ancestors if store.get_idea(a)]
        return ok_response({"idea_id": idea_id, "ancestors": ideas})
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/ideas/<idea_id>/descendants")
def get_descendants(idea_id: str):
    """Get all descendant ideas."""
    if not lineage_graph.has_idea(idea_id):
        return error_response(f"Idea '{idea_id}' not found in graph", 404)
    try:
        descendants = lineage_graph.get_descendants(idea_id)
        ideas = [store.get_idea(d).to_dict() for d in descendants if store.get_idea(d)]
        return ok_response({"idea_id": idea_id, "descendants": ideas})
    except ValueError as exc:
        return error_response(str(exc))


# ═══ AI Predictions ══════════════════════════════════════════════

@app.route("/api/predictions/dormant")
def get_dormant_ideas():
    """Identify dormant ideas with multi-feature scoring."""
    threshold = request.args.get("threshold", 0.45, type=float)
    dormant = prediction_service.get_dormant_ideas(threshold=threshold)
    return ok_response(dormant)


@app.route("/api/predictions/similar/<idea_id>")
def get_similar_ideas(idea_id: str):
    """Find similar ideas using TF-IDF cosine similarity."""
    if store.get_idea(idea_id) is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    top_n = request.args.get("top_n", 5, type=int)
    try:
        similar = prediction_service.get_similar_ideas(idea_id, top_n=top_n)
        return ok_response(similar)
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/predictions/forecast/<idea_id>")
def get_forecast(idea_id: str):
    """Forecast evolution stage with confidence and explanation."""
    if store.get_idea(idea_id) is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    try:
        forecast = prediction_service.forecast_idea(idea_id)
        return ok_response(forecast)
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/predictions/overview")
def get_predictions_overview():
    """Combined prediction dashboard data."""
    overview = prediction_service.get_prediction_overview()
    return ok_response(overview)


# ═══ Dataset Export ══════════════════════════════════════════════

@app.route("/api/export/dataset")
def export_dataset():
    """Export dataset in CSV, JSON, or graph format."""
    fmt = request.args.get("format", "json").lower()
    if fmt == "csv":
        data = dataset_exporter.export_csv()
        return ok_response(data)
    elif fmt == "json":
        data = dataset_exporter.export_json()
        return ok_response(data)
    elif fmt == "graph":
        data = dataset_exporter.export_graph()
        return ok_response(data)
    else:
        return error_response(f"Unsupported format '{fmt}'. Use csv, json, or graph.")


# ═══ Statistics ══════════════════════════════════════════════════

@app.route("/api/stats")
def get_stats():
    """Get dashboard statistics."""
    ideas = store.get_all_ideas()
    graph_stats = lineage_graph.get_stats()

    stage_counts = {}
    for stage in EvolutionStage:
        stage_counts[stage.value] = len(store.get_ideas_by_stage(stage))

    categories = {}
    for idea in ideas:
        categories[idea.category] = categories.get(idea.category, 0) + 1

    years = [i.start_year for i in ideas]

    # Get storage info from DataStore
    store_stats = store.get_stats()

    return ok_response({
        "total_ideas": len(ideas),
        "total_edges": graph_stats["total_edges"],
        "evolution_stages": stage_counts,
        "categories": categories,
        "earliest_year": min(years) if years else None,
        "latest_year": max(years) if years else None,
        "is_dag": graph_stats.get("is_dag", True),
        "evolution_chains": 8,
        "storage": store_stats.get("storage", "unknown"),
    })


# ═══ LLM Idea Generation ════════════════════════════════════════

@app.route("/api/ideas/generate", methods=["POST"])
def generate_idea():
    """Generate a full idea using LLM from just a name and optional description.

    Accepts: { "idea": "Quantum Entanglement", "description": "optional..." }
    Uses Gemini to determine stage, category, year, keywords, laureates, etc.
    """
    data = request.get_json()
    if not data or "idea" not in data:
        return error_response("'idea' field required in request body")

    idea_name = data["idea"].strip()
    user_desc = data.get("description", "").strip()

    if not llm_service.is_configured():
        return error_response(
            "OPENAI_API_KEY environment variable is not set.",
            503
        )

    try:
        api_key = os.getenv("OPENAI_API_KEY")

        prompt = f"""You are a scholarly research assistant. Given an idea/concept name, generate structured metadata about it for a Theory-to-Reality Evolution Tracker.

Idea Name: {idea_name}
{f'User Description: {user_desc}' if user_desc else ''}

Generate the following JSON (and NOTHING else) with these fields:
{{
  "title": "{idea_name}",
  "description": "A scholarly 3-5 sentence description of this idea, its significance, and impact (50-120 words, plain text, no markdown)",
  "stage": "one of: philosophy, scientific_validation, engineering_application, modern_technology",
  "category": "one of: Physics, Chemistry, Biology, Mathematics, Computer science, Medicine, Economics, Psychology, Neuroscience, Astronomy, Engineering, Genetics, Artificial intelligence, General Science",
  "start_year": <integer year when this idea first emerged>,
  "end_year": <integer year or null if still active>,
  "laureates": ["key contributors or pioneers, 1-4 names"],
  "keywords": ["3-6 relevant lowercase keywords"],
  "influence_score": <float 0.0-1.0 based on global impact>,
  "motivation": "one sentence about why this idea matters"
}}

Rules:
- stage should reflect the CURRENT state of this idea
- start_year must be a reasonable historical year
- Return ONLY valid JSON, no markdown fences, no extra text"""

        llm_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 800},
            timeout=30,
        )
        if llm_response.status_code != 200:
            return error_response(f"OpenAI API error: {llm_response.text[:200]}", 502)

        generated_text = llm_response.json()["choices"][0]["message"]["content"].strip()

        # Extract JSON from response
        import json as json_lib

        # Strip markdown fences if present
        if generated_text.startswith("```"):
            lines = generated_text.split("\n")
            generated_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            generated_text = generated_text.strip()

        json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
        if json_match:
            generated_text = json_match.group(0)

        idea_data = json_lib.loads(generated_text)

        # Build a safe ID
        safe_id = re.sub(r'[^a-z0-9]+', '_', idea_name.lower()).strip('_')[:60]
        safe_id += f"_{idea_data.get('start_year', 2000)}"

        # Validate stage
        stage_str = idea_data.get("stage", "philosophy")
        if stage_str not in ["philosophy", "scientific_validation", "engineering_application", "modern_technology"]:
            stage_str = "philosophy"

        # Create IdeaNode
        idea = IdeaNode(
            id=safe_id,
            title=idea_data.get("title", idea_name),
            description=idea_data.get("description", f"Concept of {idea_name}"),
            stage=EvolutionStage.from_string(stage_str),
            start_year=int(idea_data.get("start_year", 2000)),
            end_year=int(idea_data["end_year"]) if idea_data.get("end_year") else None,
            category=idea_data.get("category", "General Science"),
            laureates=idea_data.get("laureates", ["Unknown"]),
            motivation=idea_data.get("motivation", f"Scholarly concept: {idea_name}"),
            keywords=idea_data.get("keywords", [idea_name.lower()]),
            influence_score=min(1.0, max(0.0, float(idea_data.get("influence_score", 0.5)))),
        )

        store.add_idea(idea)

        # Also add to in-memory data structures
        try:
            lineage_graph.add_idea(idea)
        except ValueError:
            pass  # duplicate
        s = idea.start_year
        e = idea.end_year or s
        interval_tree.insert(s, e, idea.id)
        segment_tree.update(s, e)

        # Automatically create evolutionary edges
        _create_evolutionary_edges_for_new_idea(idea)

        return ok_response(idea.to_dict(), "Idea generated with AI and saved"), 201

    except json_lib.JSONDecodeError as exc:
        return error_response(f"Failed to parse LLM response as JSON: {str(exc)}", 500)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to generate idea: {str(exc)}", 500)


# ═══ Edges ═══════════════════════════════════════════════════════

@app.route("/api/edges", methods=["POST"])
def create_edge():
    """Create a new influence edge."""
    data = request.get_json()
    if not data:
        return error_response("Request body required")
    try:
        edge = InfluenceEdge(
            source_id=data["source_id"],
            target_id=data["target_id"],
            influence_type=data.get("influence_type", "derived_from"),
            influence_weight=data.get("influence_weight", 0.5),
            evidence=data.get("evidence", ""),
            confidence_score=data.get("confidence_score", 0.5),
        )
        store.add_edge(edge)
        lineage_graph.add_influence(edge)
        return ok_response(edge.to_dict(), "Edge created"), 201
    except (ValueError, KeyError) as exc:
        return error_response(str(exc))


# ═══ NLP Analysis ════════════════════════════════════════════════

@app.route("/api/nlp/keywords/<idea_id>")
def get_nlp_keywords(idea_id: str):
    """Extract keywords from an idea using TF-IDF."""
    if store.get_idea(idea_id) is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    top_n = request.args.get("top_n", 8, type=int)
    try:
        keywords = nlp_service.extract_keywords_for_idea(idea_id, top_n=top_n)
        return ok_response(keywords)
    except ValueError as exc:
        return error_response(str(exc))


@app.route("/api/nlp/classify", methods=["POST"])
def classify_stage():
    """Classify evolution stage from text."""
    data = request.get_json()
    if not data or "text" not in data:
        return error_response("'text' field required in request body")
    result = nlp_service.classify_stage(data["text"])
    return ok_response(result)


@app.route("/api/nlp/analyze")
def nlp_analyze_all():
    """Run NLP analysis on all ideas (keywords, stage prediction, NER)."""
    results = nlp_service.analyze_all_ideas()
    correct = sum(1 for r in results if r["stage_match"])
    total = len(results)
    return ok_response({
        "analyses": results,
        "accuracy": round(correct / total, 4) if total > 0 else 0,
        "correct_predictions": correct,
        "total_ideas": total,
    })


# ═══ LLM Summarizer ══════════════════════════════════════════════

@app.route("/api/llm/summarize/<idea_id>", methods=["POST"])
def llm_summarize(idea_id: str):
    """Generate an AI-powered description for a single idea using Gemini."""
    if not llm_service.is_configured():
        return error_response(
            "OPENAI_API_KEY environment variable is not set.",
            503
        )
    idea = store.get_idea(idea_id)
    if idea is None:
        return error_response(f"Idea '{idea_id}' not found", 404)
    try:
        result = llm_service.summarize_idea(idea_id)
        return ok_response(result, "Description generated successfully")
    except RuntimeError as exc:
        return error_response(str(exc), 502)
    except ValueError as exc:
        return error_response(str(exc), 404)


@app.route("/api/llm/summarize-batch", methods=["POST"])
def llm_summarize_batch():
    """Generate AI descriptions for multiple ideas (max 10)."""
    if not llm_service.is_configured():
        return error_response(
            "OPENAI_API_KEY environment variable is not set.",
            503
        )
    data = request.get_json()
    if not data or "idea_ids" not in data:
        return error_response("'idea_ids' list required in request body")
    try:
        result = llm_service.summarize_batch(data["idea_ids"])
        return ok_response(result, f"Processed {result['processed']} ideas")
    except RuntimeError as exc:
        return error_response(str(exc), 502)


@app.route("/api/llm/status")
def llm_status():
    """Check if the LLM service is configured."""
    configured = llm_service.is_configured()
    return ok_response({
        "configured": configured,
        "model": llm_service._model,
        "message": "Ready" if configured else "OPENAI_API_KEY not set",
    })


# ═══ Idea Chat (AI Research Assistant) ═══════════════════════════

@app.route("/api/ideas/<idea_id>/chat", methods=["POST"])
def chat_about_idea(idea_id: str):
    """Chat with an AI research assistant about a specific idea.

    Accepts: { "message": "user question", "history": [{"role":"user","content":"..."}, ...] }
    Returns: { "reply": "AI response text" }
    """
    # Check LLM availability
    if not llm_service.is_configured():
        return error_response(
            "OPENAI_API_KEY environment variable is not set.",
            503
        )

    # Find the idea — check both local store and MongoDB
    idea = store.get_idea(idea_id)
    idea_context = None

    if idea:
        idea_context = {
            "title": idea.title,
            "description": idea.description,
            "category": idea.category,
            "stage": idea.stage.value if hasattr(idea.stage, 'value') else str(idea.stage),
            "start_year": idea.start_year,
            "end_year": idea.end_year,
            "laureates": idea.laureates,
            "keywords": idea.keywords,
            "influence_score": idea.influence_score,
        }
    else:
        # Try MongoDB / Yugas ideas — use targeted lookup instead of loading ALL ideas
        try:
            from flask import g
            # First try exact name lookup (fast, single MongoDB query)
            mongo_idea = mongo_service.get_idea_by_name(idea_id, user_id=g.user_id)
            if mongo_idea and isinstance(mongo_idea, dict):
                idea_context = {
                    "title": mongo_idea.get("idea", mongo_idea.get("title", idea_id)),
                    "description": mongo_idea.get("description", ""),
                    "category": mongo_idea.get("category", "General"),
                    "stage": mongo_idea.get("current_stage", mongo_idea.get("stage", "unknown")),
                    "start_year": mongo_idea.get("start_year", mongo_idea.get("origin_year", "unknown")),
                    "end_year": mongo_idea.get("end_year"),
                    "laureates": mongo_idea.get("laureates", mongo_idea.get("key_figures", [])),
                    "keywords": mongo_idea.get("keywords", []),
                    "influence_score": mongo_idea.get("influence_score", 0.5),
                }
        except Exception:
            pass

    if not idea_context:
        # Even without idea context, allow chat with just the idea_id as a topic
        idea_context = {
            "title": idea_id.replace("_", " ").title(),
            "description": "",
            "category": "General",
            "stage": "unknown",
            "start_year": "unknown",
            "end_year": None,
            "laureates": [],
            "keywords": [],
            "influence_score": 0.5,
        }

    data = request.get_json()
    if not data or "message" not in data:
        return error_response("'message' field required in request body")

    user_message = data["message"].strip()
    history = data.get("history", [])

    if not user_message:
        return error_response("Message cannot be empty")

    # Build the system context prompt
    laureates_str = ", ".join(idea_context["laureates"]) if idea_context["laureates"] else "Various contributors"
    keywords_str = ", ".join(idea_context["keywords"]) if idea_context["keywords"] else "Not specified"
    year_str = str(idea_context["start_year"])
    if idea_context.get("end_year"):
        year_str += f" – {idea_context['end_year']}"

    system_prompt = f"""You are an expert AI research assistant specializing in the study and analysis of ideas, theories, and their evolution. You are currently helping a researcher explore a specific idea in depth.

IDEA CONTEXT:
- Title: {idea_context['title']}
- Category: {idea_context['category']}
- Evolution Stage: {idea_context['stage']}
- Time Period: {year_str}
- Key Contributors: {laureates_str}
- Keywords: {keywords_str}
- Description: {idea_context['description'][:500] if idea_context['description'] else 'Not available'}
- Influence Score: {idea_context['influence_score']}

INSTRUCTIONS:
- Answer questions specifically about this idea, its history, significance, applications, and related concepts
- Provide scholarly, well-researched responses with historical context
- If the user asks about connections to other ideas, explain how they relate
- Be conversational but informative — like a knowledgeable professor
- Keep responses concise but thorough (2-4 paragraphs max unless more detail is requested)
- If you don't know something, say so honestly rather than making things up
- Use plain text formatting, no markdown"""

    try:
        api_key = os.getenv("OPENAI_API_KEY")

        # Build conversation messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 10 turns max to stay within token limits)
        recent_history = history[-10:] if len(history) > 10 else history
        for msg in recent_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        # Add current message
        messages.append({"role": "user", "content": user_message})

        llm_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.7, "max_tokens": 1000},
            timeout=30,
        )

        if llm_response.status_code != 200:
            raise RuntimeError(f"OpenAI API error {llm_response.status_code}: {llm_response.text[:200]}")

        reply_text = llm_response.json()["choices"][0]["message"]["content"].strip()

        # Persist both messages to MongoDB
        from flask import g
        mongo_service.save_chat_message(g.user_id, idea_id, "user", user_message)
        mongo_service.save_chat_message(g.user_id, idea_id, "assistant", reply_text)

        return ok_response({
            "reply": reply_text,
            "idea_title": idea_context["title"],
            "model": llm_service._model,
        }, "Chat response generated")

    except Exception as exc:
        error_msg = str(exc)
        # Handle rate limits gracefully
        if any(kw in error_msg for kw in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "quota", "rate limit"]):
            fallback_reply = "I'm currently experiencing high demand. Please try again in a few seconds. The AI service has temporary rate limits."
            # Still persist the user message and fallback reply
            from flask import g
            mongo_service.save_chat_message(g.user_id, idea_id, "user", user_message)
            mongo_service.save_chat_message(g.user_id, idea_id, "assistant", fallback_reply)
            return ok_response({
                "reply": fallback_reply,
                "idea_title": idea_context["title"],
                "model": "fallback",
            }, "Rate limited — fallback response")

        import traceback
        traceback.print_exc()
        return error_response(f"Chat failed: {error_msg}", 500)


@app.route("/api/ideas/<idea_id>/chat/history", methods=["GET"])
def get_chat_history(idea_id: str):
    """Get persisted chat history for an idea."""
    from flask import g
    limit = request.args.get("limit", 50, type=int)
    messages = mongo_service.get_chat_history(g.user_id, idea_id, limit=limit)
    return ok_response({"messages": messages, "idea_id": idea_id, "count": len(messages)})


@app.route("/api/ideas/<idea_id>/chat/history", methods=["DELETE"])
def clear_chat_history_route(idea_id: str):
    """Clear chat history for an idea."""
    from flask import g
    mongo_service.clear_chat_history(g.user_id, idea_id)
    return ok_response(None, "Chat history cleared")


@app.route("/api/predictions/future-ideas", methods=["POST"])
def predict_future_ideas():
    """Generate predictions for future breakthrough ideas using LLM or fallback."""
    import json as json_lib
    import random
    
    data = request.get_json()
    category = data.get("category", "Computer Science") if data else "Computer Science"
    count = data.get("count", 5) if data else 5
    count = min(count, 10)  # Max 10 predictions
    
    # Get recent ideas in the category for context
    all_ideas = store.get_all_ideas()
    category_ideas = [i for i in all_ideas if category.lower() in i.category.lower()]
    recent_ideas = sorted(category_ideas, key=lambda x: x.start_year, reverse=True)[:10]
    
    # Try LLM first if configured
    if llm_service.is_configured():
        try:
            client = llm_service._get_client()
            
            # Build context from recent ideas
            context_text = "\n".join([
                f"- {idea.title} ({idea.start_year}): {idea.description[:100]}..."
                for idea in recent_ideas[:5]
            ])
            
            prompt = f"""You are a futurist and technology researcher. Based on the current trends in {category}, 
predict {count} breakthrough ideas that could emerge in the next 10-20 years.

Recent developments in {category}:
{context_text}

Generate {count} future breakthrough ideas. For each idea, provide:
1. A compelling title (5-10 words)
2. A brief description (2-3 sentences explaining the concept and its potential impact)
3. Estimated timeframe (e.g., "2025-2030", "2030-2035")
4. Key enabling technologies or prerequisites

Format your response as a JSON array with this structure:
[
  {{
    "title": "Idea title",
    "description": "Detailed description of the breakthrough idea and its impact",
    "timeframe": "2025-2030",
    "prerequisites": ["Technology 1", "Technology 2"],
    "category": "{category}",
    "confidence": 0.75
  }}
]

Be creative but grounded in current technological trajectories. Focus on ideas that could realistically emerge from current research directions.

Return ONLY the JSON array, no additional text."""

            response = client.models.generate_content(
                model=llm_service._model,
                contents=prompt,
            )
            
            generated_text = response.text.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', generated_text, re.DOTALL)
            if json_match:
                generated_text = json_match.group(0)
            
            # Parse the JSON response
            predictions = json_lib.loads(generated_text)
            
            return ok_response({
                "category": category,
                "predictions": predictions,
                "count": len(predictions),
                "model": llm_service._model,
                "context_ideas": len(recent_ideas),
                "source": "llm"
            })
            
        except Exception as exc:
            error_msg = str(exc)
            # Check for rate limit or quota errors
            if any(keyword in error_msg for keyword in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "quota", "rate limit"]):
                # Fall through to fallback
                print(f"LLM unavailable (rate limit/quota): {error_msg[:100]}")
            else:
                # If it's not a rate limit error, return the error
                return error_response(f"Failed to generate predictions: {error_msg}", 500)
    
    # Fallback: Generate rule-based predictions
    predictions = _generate_fallback_predictions(category, count, recent_ideas)
    
    return ok_response({
        "category": category,
        "predictions": predictions,
        "count": len(predictions),
        "model": "rule-based-fallback",
        "context_ideas": len(recent_ideas),
        "source": "fallback"
    })


def _generate_fallback_predictions(category: str, count: int, recent_ideas: list) -> list:
    """Generate rule-based future predictions when LLM is unavailable."""
    import random
    
    # Category-specific prediction templates
    templates = {
        "Computer Science": [
            {
                "title": "Quantum Neural Networks",
                "description": "Integration of quantum computing principles with deep learning architectures, enabling exponentially faster training and inference for complex AI models. This breakthrough could revolutionize machine learning by solving problems currently intractable for classical computers.",
                "timeframe": "2027-2032",
                "prerequisites": ["Quantum Computing", "Deep Learning", "Quantum Algorithms"],
                "confidence": 0.78
            },
            {
                "title": "Neuromorphic Computing Chips",
                "description": "Brain-inspired processors that mimic biological neural structures, offering ultra-low power consumption and real-time learning capabilities. These chips could enable truly intelligent edge devices and autonomous systems.",
                "timeframe": "2026-2030",
                "prerequisites": ["Neuroscience", "Semiconductor Technology", "Machine Learning"],
                "confidence": 0.82
            },
            {
                "title": "Autonomous Code Generation Systems",
                "description": "AI systems capable of writing, testing, and deploying production-ready code from natural language specifications. This could democratize software development and accelerate innovation across all industries.",
                "timeframe": "2028-2033",
                "prerequisites": ["Large Language Models", "Software Engineering", "Formal Verification"],
                "confidence": 0.75
            },
            {
                "title": "Holographic Computing Interfaces",
                "description": "Three-dimensional interactive displays that allow manipulation of digital objects in physical space without special glasses. This technology could transform how we interact with computers and collaborate remotely.",
                "timeframe": "2030-2035",
                "prerequisites": ["Photonics", "Computer Vision", "Haptic Technology"],
                "confidence": 0.68
            },
            {
                "title": "Distributed Consciousness Networks",
                "description": "Brain-computer interfaces enabling direct neural communication between multiple individuals, creating shared cognitive experiences and collaborative problem-solving at the speed of thought.",
                "timeframe": "2035-2040",
                "prerequisites": ["Brain-Computer Interfaces", "Neuroscience", "Wireless Technology"],
                "confidence": 0.55
            }
        ],
        "Physics": [
            {
                "title": "Room Temperature Superconductors",
                "description": "Materials that conduct electricity without resistance at ambient temperatures, revolutionizing power transmission, magnetic levitation, and quantum computing. This breakthrough could eliminate energy losses in electrical grids worldwide.",
                "timeframe": "2028-2033",
                "prerequisites": ["Materials Science", "Condensed Matter Physics", "Quantum Mechanics"],
                "confidence": 0.72
            },
            {
                "title": "Controlled Nuclear Fusion Reactors",
                "description": "Commercially viable fusion power plants that generate clean, abundant energy by replicating the sun's power source. This could solve the global energy crisis and eliminate dependence on fossil fuels.",
                "timeframe": "2030-2035",
                "prerequisites": ["Plasma Physics", "Materials Engineering", "Magnetic Confinement"],
                "confidence": 0.80
            },
            {
                "title": "Gravitational Wave Communication",
                "description": "Communication systems using gravitational waves instead of electromagnetic radiation, enabling instantaneous data transmission through any medium and potentially across vast cosmic distances.",
                "timeframe": "2040-2050",
                "prerequisites": ["General Relativity", "Quantum Gravity", "Advanced Detectors"],
                "confidence": 0.45
            },
            {
                "title": "Metamaterial Cloaking Devices",
                "description": "Engineered materials that bend light and other electromagnetic waves around objects, making them effectively invisible. Applications range from stealth technology to advanced optical devices.",
                "timeframe": "2027-2032",
                "prerequisites": ["Metamaterials", "Optics", "Nanotechnology"],
                "confidence": 0.70
            },
            {
                "title": "Quantum Entanglement Networks",
                "description": "Large-scale quantum networks leveraging entanglement for ultra-secure communication and distributed quantum computing. This could create an unhackable quantum internet.",
                "timeframe": "2029-2034",
                "prerequisites": ["Quantum Mechanics", "Photonics", "Quantum Information Theory"],
                "confidence": 0.76
            }
        ],
        "Medicine": [
            {
                "title": "Personalized Cancer Vaccines",
                "description": "Custom-designed vaccines that train the immune system to recognize and destroy cancer cells specific to each patient's tumor. This approach could transform cancer from a deadly disease to a manageable condition.",
                "timeframe": "2026-2030",
                "prerequisites": ["Immunotherapy", "Genomics", "mRNA Technology"],
                "confidence": 0.85
            },
            {
                "title": "Nanobots for Targeted Drug Delivery",
                "description": "Microscopic robots that navigate the bloodstream to deliver drugs precisely to diseased cells, minimizing side effects and maximizing treatment efficacy. This could revolutionize how we treat diseases at the cellular level.",
                "timeframe": "2030-2035",
                "prerequisites": ["Nanotechnology", "Bioengineering", "Medical Imaging"],
                "confidence": 0.73
            },
            {
                "title": "Organ Regeneration Therapy",
                "description": "Techniques to stimulate the body's natural ability to regrow damaged organs using stem cells and growth factors, eliminating the need for transplants and donor organs.",
                "timeframe": "2032-2037",
                "prerequisites": ["Stem Cell Research", "Tissue Engineering", "Developmental Biology"],
                "confidence": 0.68
            },
            {
                "title": "AI-Powered Diagnostic Systems",
                "description": "Artificial intelligence that can diagnose diseases with superhuman accuracy by analyzing medical images, genetic data, and patient history. This could democratize access to expert-level medical care globally.",
                "timeframe": "2025-2029",
                "prerequisites": ["Machine Learning", "Medical Imaging", "Big Data Analytics"],
                "confidence": 0.88
            },
            {
                "title": "Longevity Extension Treatments",
                "description": "Therapies that target the biological mechanisms of aging, potentially extending healthy human lifespan by decades. This could fundamentally change society's relationship with aging and mortality.",
                "timeframe": "2035-2045",
                "prerequisites": ["Gerontology", "Genetics", "Cellular Biology"],
                "confidence": 0.60
            }
        ],
        "Biology": [
            {
                "title": "Synthetic Life Forms",
                "description": "Artificially created organisms with custom-designed genomes for specific purposes like environmental cleanup, biofuel production, or pharmaceutical manufacturing. This could open entirely new frontiers in biotechnology.",
                "timeframe": "2028-2033",
                "prerequisites": ["Synthetic Biology", "Genetic Engineering", "Systems Biology"],
                "confidence": 0.70
            },
            {
                "title": "Brain-to-Brain Communication",
                "description": "Direct neural interfaces enabling thought transmission between individuals without language, creating new forms of human connection and collaboration.",
                "timeframe": "2032-2037",
                "prerequisites": ["Neuroscience", "Brain-Computer Interfaces", "Signal Processing"],
                "confidence": 0.65
            },
            {
                "title": "Ecosystem Restoration Technology",
                "description": "Biotechnology tools to rapidly restore damaged ecosystems by reintroducing extinct species, repairing soil microbiomes, and accelerating natural recovery processes.",
                "timeframe": "2027-2032",
                "prerequisites": ["Ecology", "Genetic Engineering", "Conservation Biology"],
                "confidence": 0.75
            },
            {
                "title": "Photosynthesis Enhancement",
                "description": "Genetic modifications to crops that dramatically increase photosynthetic efficiency, potentially doubling food production while reducing water and fertilizer needs.",
                "timeframe": "2026-2031",
                "prerequisites": ["Plant Biology", "Genetic Engineering", "Biochemistry"],
                "confidence": 0.80
            },
            {
                "title": "Consciousness Transfer Technology",
                "description": "Methods to map and potentially transfer human consciousness to artificial substrates, raising profound questions about identity, mortality, and the nature of existence.",
                "timeframe": "2040-2050",
                "prerequisites": ["Neuroscience", "Computer Science", "Philosophy of Mind"],
                "confidence": 0.40
            }
        ]
    }
    
    # Default template for categories not in the dictionary
    default_template = [
        {
            "title": f"Advanced {category} Integration Systems",
            "description": f"Next-generation systems that integrate cutting-edge {category} principles with artificial intelligence and quantum computing, enabling breakthrough applications previously thought impossible.",
            "timeframe": "2028-2033",
            "prerequisites": [category, "Artificial Intelligence", "Quantum Computing"],
            "confidence": 0.70
        },
        {
            "title": f"Sustainable {category} Solutions",
            "description": f"Environmentally friendly approaches to {category} that minimize resource consumption while maximizing efficiency and impact, addressing global sustainability challenges.",
            "timeframe": "2026-2031",
            "prerequisites": [category, "Environmental Science", "Green Technology"],
            "confidence": 0.75
        },
        {
            "title": f"Decentralized {category} Networks",
            "description": f"Distributed systems leveraging blockchain and peer-to-peer technologies to democratize access to {category} resources and eliminate centralized control.",
            "timeframe": "2027-2032",
            "prerequisites": [category, "Blockchain", "Network Theory"],
            "confidence": 0.68
        },
        {
            "title": f"Biomimetic {category} Applications",
            "description": f"Technologies inspired by biological systems that apply nature's solutions to {category} challenges, creating more efficient and adaptive systems.",
            "timeframe": "2029-2034",
            "prerequisites": [category, "Biology", "Biomimetics"],
            "confidence": 0.72
        },
        {
            "title": f"Cognitive {category} Assistants",
            "description": f"AI-powered systems that augment human capabilities in {category}, providing real-time insights, predictions, and decision support.",
            "timeframe": "2025-2030",
            "prerequisites": [category, "Machine Learning", "Human-Computer Interaction"],
            "confidence": 0.78
        }
    ]
    
    # Get templates for the category
    category_templates = templates.get(category, default_template)
    
    # Select random predictions up to count
    selected = random.sample(category_templates, min(count, len(category_templates)))
    
    # Add category to each prediction
    for pred in selected:
        pred["category"] = category
    
    return selected


# ═══ Yugas Evolution ═════════════════════════════════════════════
# (Services already initialized above: mongo_service, yuga_generator, yuga_ds)


def _ensure_yuga_structures():
    """Lazily load Yuga data structures for the current user when a Yuga endpoint is hit."""
    from flask import g
    if hasattr(g, 'context') and g.context:
        g.context.load_yuga_structures(mongo_service)

@app.route("/api/yugas/generate", methods=["POST"])
def generate_yuga_evolution():
    """Generate Yuga evolution for a single idea."""
    data = request.get_json()
    if not data or "idea" not in data:
        return error_response("'idea' field required in request body")
    
    idea_name = data["idea"]
    description = data.get("description", "")
    source = data.get("source", "Manual")
    
    try:
        # Generate Yuga evolution
        record = yuga_generator.create_yuga_record(idea_name, description, source)
        
        # Store in MongoDB (upsert — updates if already exists)
        from flask import g
        record_id = mongo_service.insert_idea(record, user_id=g.user_id)
        
        if record_id:
            # Reload data structures so the new idea is in the lineage graph
            g.context.yuga_loaded = False
            g.context.load_yuga_structures(mongo_service)
            return ok_response(record, "Yuga evolution generated and saved")
        else:
            return ok_response(record, "Yuga evolution generated (save failed, returned anyway)")
            
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to generate Yuga evolution: {str(exc)}", 500)


@app.route("/api/yugas/fetch-and-generate", methods=["POST"])
def fetch_and_generate_yugas():
    """Fetch ideas from online sources and generate Yuga evolutions."""
    data = request.get_json() or {}
    source = data.get("source", "wikipedia")  # wikipedia, github
    limit = min(data.get("limit", 5), 20)  # Max 20 at a time
    
    try:
        # Fetch ideas based on source
        if source == "wikipedia":
            ideas = yuga_generator.fetch_ideas_from_wikipedia(limit)
        elif source == "github":
            ideas = yuga_generator.fetch_ideas_from_github(limit)
        else:
            return error_response(f"Unknown source: {source}. Use 'wikipedia' or 'github'")
        
        # Generate and store Yuga evolutions
        from flask import g
        results = []
        for idea in ideas:
            try:
                record = yuga_generator.create_yuga_record(
                    idea["name"],
                    idea["description"],
                    idea["source"]
                )
                record_id = mongo_service.insert_idea(record, user_id=g.user_id)
                results.append({
                    "idea": idea["name"],
                    "stored": record_id is not None,
                    "record_id": record_id
                })
            except Exception as e:
                print(f"Error processing {idea['name']}: {e}")
                results.append({
                    "idea": idea["name"],
                    "stored": False,
                    "error": str(e)
                })
        
        # Reload data structures so the new ideas are in the lineage graph
        g.context.yuga_loaded = False
        g.context.load_yuga_structures(mongo_service)
        return ok_response(results, "Bulk generation completed")
    except Exception as exc:
        return error_response(f"Bulk generation failed: {str(exc)}", 500)


@app.route("/api/yugas/ideas")
def get_yuga_ideas():
    """Get all Yuga evolution ideas for the current user."""
    limit = min(request.args.get("limit", 200, type=int), 1000)
    try:
        from flask import g
        try:
            ideas = mongo_service.get_all_ideas(limit=limit, user_id=g.user_id)
        except Exception as db_error:
            print(f"MongoDB error: {db_error}")
            ideas = []
            fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
            if fallback_file.exists():
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    ideas = json.load(f)
                    
        # Filter out _id if it's there
        for idea in ideas:
            if isinstance(idea, dict):
                idea.pop("_id", None)
                
        return ok_response({"ideas": ideas})
    except Exception as exc:
        return error_response(f"Failed to load Yuga ideas: {str(exc)}", 500)


@app.route("/api/yugas/stats")
def get_yuga_stats():
    """Get Yuga evolution statistics."""
    try:
        from flask import g
        # Use MongoDB stats (count_documents) instead of loading ALL ideas
        stats = mongo_service.get_stats(user_id=g.user_id)
        return ok_response({
            "total_ideas": stats.get("total_ideas", 0),
            "categories": stats.get("categories", {}),
        })
    except Exception as exc:
        return error_response(f"Failed to get Yuga stats: {str(exc)}", 500)


@app.route("/api/yugas/search", methods=["POST"])
def search_yuga_ideas():
    """Smart semantic search for Yuga ideas using LLM."""
    data = request.get_json()
    if not data or "query" not in data:
        return error_response("'query' field required in request body")
    
    query = data["query"]
    limit = min(data.get("limit", 10), 50)
    
    try:
        from flask import g
        # Get all ideas from MongoDB or fallback
        try:
            all_ideas = mongo_service.get_all_ideas(limit=500, user_id=g.user_id)
        except Exception as db_error:
            print(f"MongoDB error: {db_error}")
            # Use fallback data from JSON
            all_ideas = []
            fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
            if fallback_file.exists():
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    all_ideas = json.load(f)
        
        if not all_ideas:
            mongo_service.log_search(g.user_id, query, "semantic", 0)
            return ok_response({"ideas": [], "count": 0})
        
        # First, do simple text matching
        simple_matches = []
        for idea in all_ideas:
            idea_name = idea.get('idea', '') if isinstance(idea, dict) else str(idea)
            idea_desc = idea.get('description', '') if isinstance(idea, dict) else ''
            idea_text = f"{idea_name} {idea_desc}".lower()
            if query.lower() in idea_text:
                simple_matches.append(idea)
        
        # If we have enough exact matches, return them immediately (skip LLM)
        if len(simple_matches) >= 1:
            mongo_service.log_search(g.user_id, query, "exact", len(simple_matches))
            return ok_response({
                "ideas": simple_matches[:limit],
                "count": len(simple_matches),
                "search_type": "exact"
            })
        
        # Use LLM for semantic search
        try:
            api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Create a summary of all ideas for the LLM
            ideas_summary = "\n".join([
                f"{i+1}. {idea.get('idea', 'Unknown') if isinstance(idea, dict) else idea}: {(idea.get('description', '')[:100] if isinstance(idea, dict) else '')}"
                for i, idea in enumerate(all_ideas[:50])
            ])
            
            prompt = f"""You are a semantic search assistant. Given a search query and a list of ideas, identify which ideas are most relevant.
 
Search Query: "{query}"
 
Available Ideas:
{ideas_summary}
 
Task: Return the numbers (1-based index) of the top 5 most relevant ideas that match the search query semantically. Consider:
- Direct matches
- Related concepts
- Similar technologies
- Connected fields
 
Return ONLY a JSON array of numbers, like: [3, 7, 12, 5, 18]
If no relevant matches, return: []"""
 
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 100
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON array
                json_match = re.search(r'\[[\d,\s]+\]', content)
                if json_match:
                    indices = json.loads(json_match.group(0))
                    
                    # Get the matched ideas (convert 1-based to 0-based index)
                    matched_ideas = []
                    for idx in indices:
                        if 1 <= idx <= len(all_ideas[:50]):
                            matched_ideas.append(all_ideas[idx - 1])
                    
                    # Combine with simple matches
                    all_matches = simple_matches + [
                        idea for idea in matched_ideas 
                        if idea not in simple_matches
                    ]
                    
                    mongo_service.log_search(g.user_id, query, "semantic", len(all_matches))
                    return ok_response({
                        "ideas": all_matches[:limit],
                        "count": len(all_matches),
                        "search_type": "semantic"
                    })
        
        except Exception as llm_error:
            print(f"LLM search error: {llm_error}")
            # Fall back to simple matches
            pass
        
        # Fallback: return simple matches or empty
        mongo_service.log_search(g.user_id, query, "fallback", len(simple_matches))
        return ok_response({
            "ideas": simple_matches[:limit],
            "count": len(simple_matches),
            "search_type": "fallback"
        })
    
    except Exception as e:
        print(f"Search error: {e}")
        return error_response(f"Search failed: {str(e)}", 500)


@app.route("/api/yugas/export-csv")
def export_yugas_csv():
    """Export all Yuga evolutions to CSV."""
    try:
        import tempfile
        import os
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()
        
        # Export to CSV
        success = mongo_service.export_to_csv(temp_file.name)
        
        if success:
            # Read file and return as response
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=yuga_evolution_export.csv'}
            )
        else:
            return error_response("No data to export", 404)
            
    except Exception as exc:
        return error_response(f"Failed to export CSV: {str(exc)}", 500)


# ─── Yugas Data Structures Endpoints ────────────────────────────

@app.route("/api/yugas/query/time-period", methods=["POST"])
def query_yugas_by_time():
    """
    Query ideas by time period using Interval Tree.
    
    Uses: Interval Tree for O(log n + k) time complexity
    
    Request body:
    {
        "start_year": -1000,  // 1000 BCE
        "end_year": 1500      // 1500 CE
    }
    """
    data = request.get_json()
    if not data or "start_year" not in data or "end_year" not in data:
        return error_response("'start_year' and 'end_year' required")
    
    try:
        _ensure_yuga_structures()
        start_year = int(data["start_year"])
        end_year = int(data["end_year"])
        
        results = yuga_ds.query_by_time_period(start_year, end_year)
        
        return ok_response({
            "ideas": results,
            "count": len(results),
            "time_period": f"{start_year} to {end_year}",
            "data_structure": "Interval Tree",
            "complexity": "O(log n + k)"
        })
    except Exception as exc:
        return error_response(f"Query failed: {str(exc)}", 500)


@app.route("/api/yugas/query/complexity", methods=["POST"])
def query_yugas_by_complexity():
    """
    Query ideas by complexity score range using Segment Tree.
    
    Uses: Segment Tree for O(log n) range queries
    
    Request body:
    {
        "min_score": 50,
        "max_score": 80,
        "yuga": "kali_yuga"  // optional
    }
    """
    data = request.get_json()
    if not data or "min_score" not in data or "max_score" not in data:
        return error_response("'min_score' and 'max_score' required")
    
    try:
        _ensure_yuga_structures()
        min_score = int(data["min_score"])
        max_score = int(data["max_score"])
        yuga = data.get("yuga", "kali_yuga")
        
        results = yuga_ds.query_by_complexity_range(min_score, max_score, yuga)
        
        return ok_response({
            "ideas": results,
            "count": len(results),
            "complexity_range": f"{min_score}-{max_score}",
            "yuga": yuga,
            "data_structure": "Segment Tree",
            "complexity": "O(log n)"
        })
    except Exception as exc:
        return error_response(f"Query failed: {str(exc)}", 500)


@app.route("/api/yugas/evolution-chain/<idea_name>")
def get_evolution_chain(idea_name: str):
    """
    Get evolution chain for an idea using Lineage Graph.
    
    Uses: Lineage Graph (Directed Acyclic Graph)
    
    Returns ancestors (what it evolved from) and descendants (what evolved from it)
    """
    try:
        _ensure_yuga_structures()
        chain = yuga_ds.get_evolution_chain(idea_name)
        
        return ok_response({
            "idea": idea_name,
            "ancestors": chain["ancestors"],
            "descendants": chain["descendants"],
            "chain_length": chain["chain_length"],
            "data_structure": "Lineage Graph (DAG)",
            "operations": "Ancestor/Descendant traversal"
        })
    except Exception as exc:
        return error_response(f"Query failed: {str(exc)}", 500)


@app.route("/api/yugas/data-structures/stats")
def get_data_structures_stats():
    """
    Get statistics about the data structures used in Yugas section.
    
    Shows why each data structure is used and their performance characteristics.
    """
    try:
        _ensure_yuga_structures()
        stats = yuga_ds.get_statistics()
        
        return ok_response({
            "statistics": stats,
            "data_structures": {
                "interval_tree": {
                    "purpose": "Time-based queries (find ideas in specific Yuga periods)",
                    "time_complexity": "O(log n + k) where k is number of results",
                    "advantage": "Much faster than linear scan O(n)",
                    "use_case": "Query all ideas from Dwapar Yuga (1000 BCE - 500 CE)"
                },
                "segment_tree": {
                    "purpose": "Range queries on complexity scores",
                    "time_complexity": "O(log n) for range queries",
                    "advantage": "Faster than sorting + binary search O(n log n)",
                    "use_case": "Find ideas with complexity 50-80 in modern era"
                },
                "lineage_graph": {
                    "purpose": "Track idea evolution chains and dependencies",
                    "structure": "Directed Acyclic Graph (DAG)",
                    "advantage": "Efficient ancestor/descendant queries vs recursive DB queries",
                    "use_case": "Show evolution: Fire → Cooking → Stove → Microwave"
                }
            }
        })
    except Exception as exc:
        return error_response(f"Failed to get stats: {str(exc)}", 500)


@app.route("/api/yugas/data-structures/reload", methods=["POST"])
def reload_data_structures():
    """
    Reload data structures with latest data from MongoDB.
    
    Call this after adding/removing ideas to rebuild indexes.
    """
    try:
        initialize_yuga_data_structures()
        stats = yuga_ds.get_statistics()
        
        return ok_response({
            "message": "Data structures reloaded successfully",
            "statistics": stats
        })
    except Exception as exc:
        return error_response(f"Reload failed: {str(exc)}", 500)


@app.route("/api/yugas/images/<path:idea_name>")
def get_yuga_images(idea_name: str):
    """
    Fetch up to 4 relevant images for an idea from its Wikipedia page.
    Returns a flat array of image URLs directly related to the idea.
    """
    try:
        from flask import g
        idea = mongo_service.get_idea_by_name(idea_name, user_id=g.user_id)
        
        # Check cached images
        if idea and idea.get("images") and len(idea["images"]) > 0:
            return ok_response({"images": idea["images"], "source": "cached"})
        
        # Run Wikipedia info and page images fetches IN PARALLEL
        from concurrent.futures import ThreadPoolExecutor, as_completed
        image_urls = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            wiki_future = executor.submit(yuga_generator.fetch_wikipedia_info, idea_name)
            images_future = executor.submit(yuga_generator.fetch_images_for_idea, idea_name)
            
            # Collect results
            try:
                wiki_info = wiki_future.result(timeout=10)
                if wiki_info.get("image_url"):
                    image_urls.append(wiki_info["image_url"])
            except Exception:
                pass
            
            try:
                page_images = images_future.result(timeout=10)
                for img in page_images:
                    if img not in image_urls:
                        image_urls.append(img)
                    if len(image_urls) >= 4:
                        break
            except Exception:
                pass
        
        # Cache in MongoDB
        if image_urls and mongo_service.is_connected() and idea:
            idea["images"] = image_urls
            mongo_service.insert_idea(idea, user_id=g.user_id)
        
        return ok_response({"images": image_urls, "source": "wikimedia"})
    
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to fetch images: {str(exc)}", 500)

# ═══ Yugas Chat (AI Cosmic Evolution Assistant) ══════════════════

@app.route("/api/yugas/chat", methods=["POST"])
def yugas_chat():
    """Chat with an AI assistant about Yugas cosmic evolution.

    Accepts: { "message": "user question", "history": [{"role":"user","content":"..."}, ...] }
    Returns: { "reply": "AI response text" }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return error_response("OPENAI_API_KEY environment variable is not set.", 503)

    data = request.get_json()
    if not data or "message" not in data:
        return error_response("'message' field required in request body")

    user_message = data["message"].strip()
    history = data.get("history", [])

    if not user_message:
        return error_response("Message cannot be empty")

    system_prompt = """You are an expert AI assistant specializing in the Yugas — the four cosmic ages from Hindu cosmology — and how modern ideas, innovations, and technologies map onto their evolution across these eras.

THE FOUR YUGAS:
- Satya Yuga (Golden Age, ~10,000 BCE – 5,000 BCE): Era of divine truth, universal harmony, effortless manifestation. Ideas existed in their purest conceptual form.
- Treta Yuga (Silver Age, ~5,000 BCE – 1,000 BCE): Era of ritual knowledge, sacred practices, and formalized wisdom held by sages and priests.
- Dwapar Yuga (Bronze Age, ~1,000 BCE – 1500 CE): Era of mechanical tools, trade guilds, practical craftsmanship, and empirical observation.
- Kali Yuga (Iron Age, ~1500 CE – Present): Era of technology, mass production, scientific method, and digital transformation.

INSTRUCTIONS:
- Answer questions about the Yugas, their significance, and how ideas evolve through them
- Explain how any concept, innovation, or technology would have manifested in each cosmic era
- Draw connections between ancient wisdom and modern science
- Be conversational, engaging, and scholarly — like a wise sage who understands both ancient philosophy and modern technology
- Keep responses concise but thorough (2-4 paragraphs max unless more detail is requested)
- Use plain text formatting, no markdown"""

    try:
        # Build conversation messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 10 turns max)
        recent_history = history[-10:] if len(history) > 10 else history
        for msg in recent_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        messages.append({"role": "user", "content": user_message})

        llm_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.7, "max_tokens": 1000},
            timeout=30,
        )

        if llm_response.status_code != 200:
            raise RuntimeError(f"OpenAI API error {llm_response.status_code}: {llm_response.text[:200]}")

        reply_text = llm_response.json()["choices"][0]["message"]["content"].strip()

        # Persist both messages to MongoDB
        from flask import g
        mongo_service.save_chat_message(g.user_id, "yugas_general", "user", user_message)
        mongo_service.save_chat_message(g.user_id, "yugas_general", "assistant", reply_text)

        return ok_response({
            "reply": reply_text,
            "model": "gpt-3.5-turbo",
        }, "Chat response generated")

    except Exception as exc:
        error_msg = str(exc)
        if any(kw in error_msg for kw in ["429", "RESOURCE_EXHAUSTED", "quota", "rate limit"]):
            fallback_reply = "I'm currently experiencing high demand. Please try again in a few seconds."
            from flask import g
            mongo_service.save_chat_message(g.user_id, "yugas_general", "user", user_message)
            mongo_service.save_chat_message(g.user_id, "yugas_general", "assistant", fallback_reply)
            return ok_response({
                "reply": fallback_reply,
                "model": "fallback",
            }, "Rate limited — fallback response")

        import traceback
        traceback.print_exc()
        return error_response(f"Chat failed: {error_msg}", 500)


@app.route("/api/yugas/chat/history", methods=["GET"])
def get_yugas_chat_history():
    """Get persisted Yugas chat history for the current user."""
    from flask import g
    limit = request.args.get("limit", 50, type=int)
    messages = mongo_service.get_chat_history(g.user_id, "yugas_general", limit=limit)
    return ok_response({"messages": messages, "count": len(messages)})


@app.route("/api/yugas/chat/history", methods=["DELETE"])
def clear_yugas_chat_history():
    """Clear Yugas chat history for the current user."""
    from flask import g
    mongo_service.clear_chat_history(g.user_id, "yugas_general")
    return ok_response(None, "Yugas chat history cleared")


# ─── Main ────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
