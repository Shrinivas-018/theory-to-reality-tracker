# Backend — Theory-to-Reality Evolution Tracker

Flask-based REST API serving 24+ endpoints with custom data structures, ML predictions, and NLP analysis.

---

## Structure

```
backend/
├── api.py                          # Flask app with all route definitions
├── models/
│   ├── evolution_stage.py          # EvolutionStage enum (4 stages)
│   ├── idea_node.py                # IdeaNode dataclass
│   ├── influence_edge.py           # InfluenceEdge dataclass
│   └── validation.py               # Input validation rules
├── data_structures/
│   ├── interval_tree.py            # BST-based interval tree
│   └── segment_tree.py             # Segment tree with lazy propagation
├── services/
│   ├── data_store.py               # JSON file persistence
│   ├── lineage_graph.py            # NetworkX DAG manager
│   ├── ai_prediction.py            # TF-IDF + RandomForest predictions
│   ├── nlp_extractor.py            # Keyword extraction & classification
│   └── dataset_exporter.py         # CSV / JSON / graph export
├── scripts/
│   └── fetch_openalex.py           # OpenAlex data ingestion script
└── tests/                          # 191 unit tests
    ├── test_models.py
    ├── test_data_store.py
    ├── test_interval_tree.py
    ├── test_segment_tree.py
    ├── test_lineage_graph.py
    ├── test_ai_prediction.py
    ├── test_nlp_extractor.py
    └── test_dataset_exporter.py
```

---

## Data Models

### EvolutionStage

Four-stage progression enum:

| Stage | Value | Description |
|-------|-------|-------------|
| `PHILOSOPHY` | `philosophy` | Initial philosophical concepts and theories |
| `SCIENTIFIC_VALIDATION` | `scientific_validation` | Experimental proof and scientific acceptance |
| `ENGINEERING_APPLICATION` | `engineering_application` | Practical engineering implementations |
| `MODERN_TECHNOLOGY` | `modern_technology` | Current technological applications |

### IdeaNode

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (alphanumeric + underscores) |
| `title` | `str` | Idea title |
| `description` | `str` | Detailed description (max 10,000 chars) |
| `stage` | `EvolutionStage` | Current evolution stage |
| `start_year` | `int` | Year introduced (1800 – current+100) |
| `end_year` | `int?` | Year reached current stage |
| `category` | `str` | Domain classification (Physics, Chemistry, etc.) |
| `laureates` | `List[str]` | Associated researchers |
| `motivation` | `str` | Reasoning or significance |
| `keywords` | `List[str]` | Descriptive keywords (≥1 required) |
| `influence_score` | `float` | Impact score (0.0 – 1.0) |

### InfluenceEdge

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | `str` | Influencing idea ID |
| `target_id` | `str` | Influenced idea ID (no self-loops) |
| `influence_type` | `str` | `derived_from`, `inspired_by`, `applied_to`, `validated_by` |
| `influence_weight` | `float` | Weight (0.0 – 1.0) |
| `evidence` | `str` | Supporting evidence (non-empty) |
| `confidence_score` | `float` | Confidence (0.0 – 1.0) |

---

## Services

### DataStore
JSON-based persistence with CRUD operations for ideas and edges. Supports cascade deletion (removing an idea also removes its edges).

### LineageGraph
NetworkX-powered DAG for tracking idea evolution relationships:
- Ancestor/descendant traversal (BFS/DFS)
- PageRank-style centrality scoring
- Shortest path between ideas
- Cycle detection (DAG validation)

### AIPredictionService
- **TF-IDF Similarity:** Cosine similarity over idea descriptions and keywords
- **Dormant Detection:** Weighted scoring (age 25%, stall 30%, connectivity 25%, tech-similarity 20%)
- **Stage Forecasting:** RandomForestClassifier (50 trees, max depth 3) with proxy labeling
- **Explainability:** Feature importance from the trained model

### NLPExtractorService
- **Keyword Extraction:** Global TF-IDF vectorization to extract top-N keywords per idea
- **Stage Classification:** Lexicon-based heuristic classification
- **NER:** Rule-based named entity extraction for scientists and labs

### DatasetExporter
Multi-format export engine producing CSV, JSON, and graph-adjacency representations.

---

## Running

```bash
# Start the API server
python -m backend.api

# Run all 191 tests
python -m pytest backend/tests/ -v

# Fetch fresh data from OpenAlex
python -m backend.scripts.fetch_openalex
```

---

## Dependencies

- Flask + Flask-CORS
- scikit-learn (TF-IDF, RandomForest)
- NetworkX (graph algorithms)
- NumPy
- pytest
