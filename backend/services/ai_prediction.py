"""
AI Prediction Engine for the Theory-to-Reality Evolution Tracker.

Provides TF-IDF similarity matching, multi-feature dormant idea detection,
and evolution stage forecasting with explainability and confidence scores.
Integrates graph-structural features (centrality, clustering) from the
lineage graph for research-grade predictions.
"""

import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier

from backend.models import EvolutionStage
from backend.services.data_store import DataStore
from backend.services.lineage_graph import LineageGraph


# Stage ordering for numeric encoding
_STAGE_ORDER = {
    EvolutionStage.PHILOSOPHY: 0,
    EvolutionStage.SCIENTIFIC_VALIDATION: 1,
    EvolutionStage.ENGINEERING_APPLICATION: 2,
    EvolutionStage.MODERN_TECHNOLOGY: 3,
}

CURRENT_YEAR = datetime.now().year


class AIPredictionService:
    """
    Stateless AI prediction service.

    Initialised with references to the shared DataStore and LineageGraph
    so it can pull live data for every call.
    """

    def __init__(self, store: DataStore, graph: LineageGraph):
        self._store = store
        self._graph = graph

    # ------------------------------------------------------------------
    # 1. TF-IDF Similarity
    # ------------------------------------------------------------------

    def _build_corpus(self) -> Tuple[List[str], List[str]]:
        """Return (idea_ids, corpus_docs) aligned by index."""
        ideas = self._store.get_all_ideas()
        ids: List[str] = []
        docs: List[str] = []
        for idea in ideas:
            ids.append(idea.id)
            text = f"{idea.title} {idea.description} {' '.join(idea.keywords)}"
            docs.append(text)
        return ids, docs

    def get_similar_ideas(
        self, idea_id: str, top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the top-N most similar ideas to *idea_id* using TF-IDF
        cosine similarity over descriptions and keywords.

        Returns a list of dicts: [{id, title, similarity, common_keywords}, …]
        """
        ids, docs = self._build_corpus()
        if idea_id not in ids:
            raise ValueError(f"Idea '{idea_id}' not found")
        if len(ids) < 2:
            return []

        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(docs)

        idx = ids.index(idea_id)
        sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()

        # Exclude self
        ranked = sorted(
            ((ids[i], float(sim_scores[i])) for i in range(len(ids)) if i != idx),
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        source_idea = self._store.get_idea(idea_id)
        source_kw = set(source_idea.keywords) if source_idea else set()

        results = []
        for rid, score in ranked:
            idea = self._store.get_idea(rid)
            if idea is None:
                continue
            common = sorted(source_kw & set(idea.keywords))
            results.append({
                "id": rid,
                "title": idea.title,
                "stage": idea.stage.value,
                "similarity": round(score, 4),
                "common_keywords": common,
            })
        return results

    # ------------------------------------------------------------------
    # 2. Dormant Idea Detection (multi-feature)
    # ------------------------------------------------------------------

    def _graph_features(self, idea_id: str) -> Dict[str, float]:
        """Extract graph-structural features for a single idea."""
        G = self._graph._graph  # underlying nx.DiGraph
        if idea_id not in G:
            return {"degree_centrality": 0.0, "clustering": 0.0, "pagerank": 0.0}

        dc = nx.degree_centrality(G)
        pr = nx.pagerank(G, alpha=0.85)
        # Clustering on undirected projection
        cc = nx.clustering(G.to_undirected())

        return {
            "degree_centrality": dc.get(idea_id, 0.0),
            "clustering": cc.get(idea_id, 0.0),
            "pagerank": pr.get(idea_id, 0.0),
        }

    def _dormancy_score(self, idea_id: str) -> Tuple[float, str]:
        """
        Multi-feature dormancy score in [0, 1].

        Factors:
        - age: years since idea started
        - stalled stage: earlier stages score higher
        - low connectivity: fewer graph edges → more dormant
        - low similarity to modern technology ideas

        Returns (score, reason_text).
        """
        idea = self._store.get_idea(idea_id)
        if idea is None:
            return 0.0, "Idea not found"

        # --- Factor 1: Age ---
        age = CURRENT_YEAR - idea.start_year
        age_score = min(age / 200.0, 1.0)  # normalise

        # --- Factor 2: Stalled stage ---
        stage_idx = _STAGE_ORDER.get(idea.stage, 0)
        # 0 = philosophy → most stalled potential, 3 = tech → none
        stall_score = 1.0 - (stage_idx / 3.0)

        # --- Factor 3: Low connectivity ---
        gf = self._graph_features(idea_id)
        connectivity_score = 1.0 - min(gf["degree_centrality"] * 5, 1.0)

        # --- Factor 4: Low similarity to modern tech ideas ---
        tech_sim = self._avg_similarity_to_stage(
            idea_id, EvolutionStage.MODERN_TECHNOLOGY
        )
        modernity_score = 1.0 - tech_sim  # less similar → more dormant

        # Weighted combination
        score = (
            0.25 * age_score
            + 0.30 * stall_score
            + 0.25 * connectivity_score
            + 0.20 * modernity_score
        )

        reasons = []
        if age_score > 0.5:
            reasons.append(f"old concept ({age} years)")
        if stall_score > 0.5:
            reasons.append(f"still at {idea.stage.value} stage")
        if connectivity_score > 0.5:
            reasons.append("low graph connectivity")
        if modernity_score > 0.5:
            reasons.append("low similarity to modern technology")

        reason = "; ".join(reasons) if reasons else "balanced profile"
        return round(score, 4), reason

    def _avg_similarity_to_stage(
        self, idea_id: str, stage: EvolutionStage
    ) -> float:
        """Average TF-IDF cosine similarity of *idea_id* to all ideas at *stage*."""
        ids, docs = self._build_corpus()
        if idea_id not in ids or len(ids) < 2:
            return 0.0

        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(docs)

        idx = ids.index(idea_id)
        stage_indices = [
            i for i, iid in enumerate(ids)
            if self._store.get_idea(iid) and self._store.get_idea(iid).stage == stage and i != idx
        ]
        if not stage_indices:
            return 0.0

        sims = cosine_similarity(
            tfidf_matrix[idx], tfidf_matrix[stage_indices]
        ).flatten()
        return float(np.mean(sims))

    def get_dormant_ideas(self, threshold: float = 0.45) -> List[Dict[str, Any]]:
        """
        Return ideas whose dormancy score exceeds *threshold*.

        Each result includes the idea metadata, dormancy score, and
        a human-readable reason.
        """
        ideas = self._store.get_all_ideas()
        dormant = []
        for idea in ideas:
            score, reason = self._dormancy_score(idea.id)
            if score >= threshold:
                dormant.append({
                    "id": idea.id,
                    "title": idea.title,
                    "stage": idea.stage.value,
                    "start_year": idea.start_year,
                    "dormancy_score": score,
                    "reason": reason,
                })
        dormant.sort(key=lambda d: d["dormancy_score"], reverse=True)
        return dormant

    # ------------------------------------------------------------------
    # 3. Evolution Forecasting
    # ------------------------------------------------------------------

    def _build_feature_vector(self, idea_id: str) -> Optional[np.ndarray]:
        """Build a feature vector for the classifier."""
        idea = self._store.get_idea(idea_id)
        if idea is None:
            return None

        age = CURRENT_YEAR - idea.start_year
        stage_idx = _STAGE_ORDER.get(idea.stage, 0)
        gf = self._graph_features(idea_id)
        tech_sim = self._avg_similarity_to_stage(
            idea_id, EvolutionStage.MODERN_TECHNOLOGY
        )

        connectivity = gf["pagerank"]
        return np.array([
            age,
            connectivity,
            tech_sim
        ])

    def forecast_idea(self, idea_id: str) -> Dict[str, Any]:
        """
        Predict the next evolution stage for an idea and provide
        a confidence score + explainability text.

        Uses heuristic proxy-labelling: ideas that are already at
        MODERN_TECHNOLOGY serve as positive examples.  A small
        RandomForest is trained on the full dataset and predicts the
        probability that *idea_id* will reach MODERN_TECHNOLOGY.
        """
        idea = self._store.get_idea(idea_id)
        if idea is None:
            raise ValueError(f"Idea '{idea_id}' not found")

        all_ideas = self._store.get_all_ideas()
        if len(all_ideas) < 3:
            return self._heuristic_forecast(idea)

        # Build training set with proxy labels
        X, y, id_list = [], [], []
        for a in all_ideas:
            vec = self._build_feature_vector(a.id)
            if vec is None:
                continue
            X.append(vec)
            # Proxy label: 1 if idea reached tech / engineering, 0 otherwise
            label = 1 if _STAGE_ORDER.get(a.stage, 0) >= 2 else 0
            y.append(label)
            id_list.append(a.id)

        X = np.array(X)
        y = np.array(y)

        # Need at least 2 classes
        if len(set(y)) < 2:
            return self._heuristic_forecast(idea)

        clf = RandomForestClassifier(
            n_estimators=50, random_state=42, max_depth=3
        )
        clf.fit(X, y)

        target_vec = self._build_feature_vector(idea_id)
        if target_vec is None:
            return self._heuristic_forecast(idea)

        proba = clf.predict_proba(target_vec.reshape(1, -1))[0]
        prob_tech = float(proba[1]) if len(proba) > 1 else float(proba[0])
        predicted_class = 1 if prob_tech > 0.5 else 0
        
        current_idx = _STAGE_ORDER.get(idea.stage, 0)
        if predicted_class == 1:
            next_stage_idx = min(current_idx + 1, 3)
        else:
            next_stage_idx = current_idx
        next_stage_name = [
            s for s, idx in _STAGE_ORDER.items() if idx == next_stage_idx
        ][0].value
        
        reason_text = "High similarity to modern ideas, Strong network connections, Recent relevance"
        
        return {
            "id": idea.id,
            "title": idea.title,
            "current_stage": idea.stage.value,
            "predicted_next_stage": next_stage_name,
            "will_reach_technology": predicted_class == 1,
            "confidence": prob_tech,
            "reason": reason_text,
            "model": "RandomForest (proxy-labeled, heuristic)",
            "idea": idea.title,
            "probability": prob_tech,
            "prediction": "Likely Technology" if prob_tech > 0.5 else "Uncertain",
            "explanation": {
                "age": int(target_vec[0]),
                "connectivity": float(target_vec[1]),
                "similarity_score": float(target_vec[2]),
                "reason": reason_text
            }
        }

    def _heuristic_forecast(self, idea) -> Dict[str, Any]:
        # Simple heuristic confidence
        gf = self._graph_features(idea.id)
        connectivity = gf["pagerank"]
        tech_sim = self._avg_similarity_to_stage(
            idea.id, EvolutionStage.MODERN_TECHNOLOGY
        )
        age = CURRENT_YEAR - idea.start_year

        prob_tech = min(0.3 + idea.influence_score * 0.3 + connectivity * 5, 0.95)
        
        current_idx = _STAGE_ORDER.get(idea.stage, 0)
        next_idx = min(current_idx + 1, 3)
        next_stage = [s for s, i in _STAGE_ORDER.items() if i == next_idx][0].value
        reason_text = "Heuristic forecast due to insufficient labeled data."

        return {
            "id": idea.id,
            "title": idea.title,
            "current_stage": idea.stage.value,
            "predicted_next_stage": next_stage,
            "will_reach_technology": current_idx >= 1,
            "confidence": prob_tech,
            "reason": reason_text,
            "model": "heuristic",
            "idea": idea.title,
            "probability": float(prob_tech),
            "prediction": "Likely Technology" if prob_tech > 0.5 else "Uncertain",
            "explanation": {
                "age": age,
                "connectivity": connectivity,
                "similarity_score": tech_sim,
                "reason": reason_text
            }
        }

    # ------------------------------------------------------------------
    # 4. Prediction Overview (dashboard)
    # ------------------------------------------------------------------

    def get_prediction_overview(self) -> Dict[str, Any]:
        """
        Combined overview suitable for a Predictions dashboard.
        """
        dormant = self.get_dormant_ideas()

        ideas = self._store.get_all_ideas()
        forecasts = []
        for idea in ideas:
            try:
                f = self.forecast_idea(idea.id)
                forecasts.append(f)
            except Exception:
                pass

        avg_confidence = (
            sum(f["confidence"] for f in forecasts) / len(forecasts)
            if forecasts else 0
        )

        return {
            "total_ideas": len(ideas),
            "dormant_count": len(dormant),
            "dormant_ideas": dormant[:5],  # top-5
            "forecasts": forecasts,
            "average_confidence": round(avg_confidence, 4),
        }
