"""
Enhanced Flask API for the Theory-to-Reality Evolution Tracker.

Provides RESTful endpoints for ideas, temporal queries, lineage graph,
AI predictions, dataset export, and dashboard statistics.
Seeds 3 evolution chains on startup.
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# Load .env file if present
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore, LineageGraph, AIPredictionService, DatasetExporter, NLPExtractorService, LLMSummarizerService
from backend.data_structures import IntervalTree, SegmentTree

import json

app = Flask(__name__)
CORS(app)

# ─── Shared state ────────────────────────────────────────────────
store = DataStore(data_dir="data/evolution_tracker_api")
interval_tree = IntervalTree()
segment_tree = SegmentTree(min_year=1800, max_year=2200)
lineage_graph = LineageGraph()
prediction_service = AIPredictionService(store, lineage_graph)
dataset_exporter = DatasetExporter(store, lineage_graph)
nlp_service = NLPExtractorService(store)
llm_service = LLMSummarizerService(store)


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


def _seed_data():
    """Load data from DataStore into in-memory temporal and graph structures."""
    ideas = store.get_all_ideas()
    edges = store.get_all_edges()

    if not ideas:
        print("⚠️ DataStore is empty. Please run 'python -m backend.scripts.fetch_openalex' to fetch the scholarly dataset.")
        return

    for idea in ideas:
        lineage_graph.add_idea(idea)

        s = idea.start_year
        e = idea.end_year or s
        interval_tree.insert(s, e, idea.id)
        segment_tree.update(s, e)

    for edge in edges:
        lineage_graph.add_influence(edge)


_seed_data()


# ═════════════════════════════════════════════════════════════════
# API Routes
# ═════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return ok_response({
        "message": "Theory-to-Reality Evolution Tracker API",
        "version": "1.0.0",
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

    return ok_response({
        "total_ideas": len(ideas),
        "total_edges": graph_stats["total_edges"],
        "evolution_stages": stage_counts,
        "categories": categories,
        "earliest_year": min(years) if years else None,
        "latest_year": max(years) if years else None,
        "is_dag": graph_stats.get("is_dag", True),
        "evolution_chains": 8,
    })


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
            "GEMINI_API_KEY environment variable is not set. "
            "Get a free key at https://aistudio.google.com/",
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
            "GEMINI_API_KEY environment variable is not set. "
            "Get a free key at https://aistudio.google.com/",
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
        "message": "Ready" if configured else "GEMINI_API_KEY not set",
    })


# ─── Main ────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
