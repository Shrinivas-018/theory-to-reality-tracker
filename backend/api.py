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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "evolution_tracker_api")
store = DataStore(data_dir=DATA_DIR)
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
            import re
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


# ─── Main ────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
