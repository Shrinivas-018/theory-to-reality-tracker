"""
Data persistence layer for storing and retrieving ideas and influence edges.

Now uses MongoDB as the primary backend with JSON file fallback.
"""

import json
import os
import time
from typing import Dict, List, Optional
from pathlib import Path

from backend.models import IdeaNode, InfluenceEdge, EvolutionStage


class DataStore:
    """
    MongoDB-backed data store for ideas and influence edges.
    
    Uses MongoDB Atlas as primary storage and falls back to JSON files
    if MongoDB is unavailable. The public API is unchanged from the
    original file-based implementation.
    """
    
    def __init__(self, data_dir: str = "data/evolution_tracker", user_id: Optional[str] = None):
        """
        Initialize the data store.
        
        Args:
            data_dir: Directory to store fallback JSON data files
            user_id: The ID of the authenticated user to isolate data
        """
        self.data_dir = Path(data_dir)
        self.user_id = user_id
        
        self.ideas_file = self.data_dir / (f"ideas_{user_id}.json" if user_id else "ideas.json")
        self.edges_file = self.data_dir / (f"edges_{user_id}.json" if user_id else "edges.json")
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self._ideas: Dict[str, IdeaNode] = {}
        self._edges: List[InfluenceEdge] = []
        
        # MongoDB state
        self._mongo_client = None
        self._mongo_db = None
        self._ideas_collection = None
        self._edges_collection = None
        self._mongo_connected = False
        
        # Try MongoDB first, then fall back to JSON
        self._try_connect_mongo()
        self._load_data()
    
    # ──────────────────────────────────────────────────────────────
    # MongoDB connection helpers
    # ──────────────────────────────────────────────────────────────
    
    def _try_connect_mongo(self):
        """Attempt to connect to MongoDB Atlas."""
        import sys
        if "pytest" in sys.modules or os.getenv("TESTING") == "True":
            # Keep tests fully isolated in their temp JSON/memory directories
            self._mongo_connected = False
            return

        try:
            from pymongo import MongoClient
        except ImportError:
            print("[WARN] pymongo not installed — DataStore using JSON fallback.")
            return
        
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        uri = os.getenv(
            "MONGODB_ATLAS_URI",
            os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        )
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
            client = MongoClient(uri, **params)
            # Test connection with retries
            for attempt in range(3):
                try:
                    client.server_info()
                    break
                except Exception:
                    if attempt < 2:
                        print(f"  [DataStore] Connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(2)
                    else:
                        raise
            
            self._mongo_client = client
            self._mongo_db = client[db_name]
            self._ideas_collection = self._mongo_db["evolution_ideas"]
            self._edges_collection = self._mongo_db["evolution_edges"]
            self._mongo_connected = True
            
            # Create indexes
            try:
                # We want multiple users to be able to have the same standard ideas
                # without clashing. We drop the old "id" unique index first if present.
                self._ideas_collection.drop_index("id_1")
            except Exception:
                pass
                
            self._ideas_collection.create_index([("id", 1), ("user_id", 1)], unique=True)
            self._ideas_collection.create_index("id") # Non-unique index for fast single ID lookup
            self._ideas_collection.create_index("user_id")
            self._ideas_collection.create_index("category")
            self._ideas_collection.create_index("stage")
            self._edges_collection.create_index([("source_id", 1), ("target_id", 1)])
            self._edges_collection.create_index("user_id")
            
            conn_type = "MongoDB Atlas" if is_atlas else "Local MongoDB"
            print(f"[OK] DataStore connected to {conn_type}: {db_name}.evolution_ideas / evolution_edges [User: {self.user_id}]")
        except Exception as e:
            print(f"[WARN] DataStore MongoDB connection failed: {e}")
            print("  Using JSON fallback for DataStore.")
            self._mongo_connected = False
    
    # ──────────────────────────────────────────────────────────────
    # Data loading
    # ──────────────────────────────────────────────────────────────
    
    def _load_data(self) -> None:
        """Load data from MongoDB or fall back to JSON files."""
        if self._mongo_connected:
            self._load_from_mongo()
        else:
            self._load_from_json()
    
    def _load_from_mongo(self) -> None:
        """Load ideas and edges from MongoDB into memory."""
        try:
            # Build queries
            query = {"user_id": self.user_id} if self.user_id else {"user_id": {"$exists": False}}
            
            # Load ideas
            for doc in self._ideas_collection.find(query):
                doc.pop("_id", None)
                try:
                    idea = IdeaNode.from_dict(doc)
                    self._ideas[idea.id] = idea
                except Exception:
                    pass  # skip malformed docs
            
            # Load edges
            for doc in self._edges_collection.find(query):
                doc.pop("_id", None)
                try:
                    edge = InfluenceEdge.from_dict(doc)
                    self._edges.append(edge)
                except Exception:
                    pass
            
            print(f"[OK] DataStore loaded {len(self._ideas)} ideas, {len(self._edges)} edges from MongoDB [User: {self.user_id}]")
            
            # If MongoDB was empty but JSON has data, seed MongoDB
            if not self._ideas and self.ideas_file.exists():
                print("[INFO] MongoDB empty, seeding from JSON files...")
                self._seed_mongo_from_json()
        except Exception as e:
            print(f"[WARN] Failed to load from MongoDB: {e}, falling back to JSON")
            self._mongo_connected = False
            self._load_from_json()
    
    def _load_from_json(self) -> None:
        """Load data from JSON files (fallback)."""
        # Load ideas
        if self.ideas_file.exists():
            with open(self.ideas_file, 'r', encoding='utf-8') as f:
                ideas_data = json.load(f)
                self._ideas = {
                    idea_id: IdeaNode.from_dict(idea_dict)
                    for idea_id, idea_dict in ideas_data.items()
                }
        
        # Load edges
        if self.edges_file.exists():
            with open(self.edges_file, 'r', encoding='utf-8') as f:
                edges_data = json.load(f)
                self._edges = [
                    InfluenceEdge.from_dict(edge_dict)
                    for edge_dict in edges_data
                ]
    
    def _seed_mongo_from_json(self) -> None:
        """One-time seed: import JSON data into MongoDB."""
        if not self._mongo_connected:
            return
        
        # Seed ideas
        if self.ideas_file.exists():
            with open(self.ideas_file, 'r', encoding='utf-8') as f:
                ideas_data = json.load(f)
            
            docs = []
            for idea_id, idea_dict in ideas_data.items():
                idea_dict["id"] = idea_id
                if self.user_id:
                    idea_dict["user_id"] = self.user_id
                docs.append(idea_dict)
            
            if docs:
                try:
                    self._ideas_collection.insert_many(docs, ordered=False)
                    print(f"[OK] Seeded {len(docs)} ideas into MongoDB")
                except Exception as e:
                    # Likely duplicate key errors — that's fine
                    print(f"[INFO] Seed ideas partial: {e}")
                
                # Reload into memory
                self._ideas.clear()
                query = {"user_id": self.user_id} if self.user_id else {"user_id": {"$exists": False}}
                for doc in self._ideas_collection.find(query):
                    doc.pop("_id", None)
                    try:
                        idea = IdeaNode.from_dict(doc)
                        self._ideas[idea.id] = idea
                    except Exception:
                        pass
        
        # Seed edges
        if self.edges_file.exists():
            with open(self.edges_file, 'r', encoding='utf-8') as f:
                edges_data = json.load(f)
            
            docs = []
            for edge_dict in edges_data:
                if self.user_id:
                    edge_dict["user_id"] = self.user_id
                docs.append(edge_dict)
            
            if docs:
                try:
                    self._edges_collection.insert_many(docs, ordered=False)
                    print(f"[OK] Seeded {len(docs)} edges into MongoDB")
                except Exception as e:
                    print(f"[INFO] Seed edges partial: {e}")
                
                self._edges.clear()
                query = {"user_id": self.user_id} if self.user_id else {"user_id": {"$exists": False}}
                for doc in self._edges_collection.find(query):
                    doc.pop("_id", None)
                    try:
                        edge = InfluenceEdge.from_dict(doc)
                        self._edges.append(edge)
                    except Exception:
                        pass
    
    # ──────────────────────────────────────────────────────────────
    # Persistence helpers
    # ──────────────────────────────────────────────────────────────
    
    def _save_data(self) -> None:
        """Save data to JSON files (always keep as backup)."""
        # Save ideas
        ideas_data = {
            idea_id: idea.to_dict()
            for idea_id, idea in self._ideas.items()
        }
        with open(self.ideas_file, 'w', encoding='utf-8') as f:
            json.dump(ideas_data, f, indent=2)
        
        # Save edges
        edges_data = [edge.to_dict() for edge in self._edges]
        with open(self.edges_file, 'w', encoding='utf-8') as f:
            json.dump(edges_data, f, indent=2)
    
    def _save_idea_to_mongo(self, idea: IdeaNode) -> None:
        """Persist a single idea to MongoDB."""
        if not self._mongo_connected:
            return
        try:
            doc = idea.to_dict()
            if self.user_id:
                doc["user_id"] = self.user_id
            
            query = {"id": idea.id}
            if self.user_id:
                query["user_id"] = self.user_id
            else:
                query["user_id"] = {"$exists": False}
                
            self._ideas_collection.replace_one(
                query,
                doc,
                upsert=True
            )
        except Exception as e:
            print(f"[WARN] MongoDB save idea failed: {e}")
    
    def _delete_idea_from_mongo(self, idea_id: str) -> None:
        """Delete a single idea from MongoDB."""
        if not self._mongo_connected:
            return
        try:
            query = {"id": idea_id}
            if self.user_id:
                query["user_id"] = self.user_id
            else:
                query["user_id"] = {"$exists": False}
            self._ideas_collection.delete_one(query)
        except Exception as e:
            print(f"[WARN] MongoDB delete idea failed: {e}")
    
    def _save_edge_to_mongo(self, edge: InfluenceEdge) -> None:
        """Persist a single edge to MongoDB."""
        if not self._mongo_connected:
            return
        try:
            doc = edge.to_dict()
            if self.user_id:
                doc["user_id"] = self.user_id
            self._edges_collection.insert_one(doc)
        except Exception as e:
            print(f"[WARN] MongoDB save edge failed: {e}")
    
    def _delete_edges_from_mongo(self, idea_id: str) -> None:
        """Delete edges referencing an idea from MongoDB."""
        if not self._mongo_connected:
            return
        try:
            query = {
                "$or": [
                    {"source_id": idea_id},
                    {"target_id": idea_id}
                ]
            }
            if self.user_id:
                query["user_id"] = self.user_id
            else:
                query["user_id"] = {"$exists": False}
            self._edges_collection.delete_many(query)
        except Exception as e:
            print(f"[WARN] MongoDB delete edges failed: {e}")
    
    # ──────────────────────────────────────────────────────────────
    # Idea operations (public API — unchanged signatures)
    # ──────────────────────────────────────────────────────────────
    
    def add_idea(self, idea: IdeaNode) -> None:
        """
        Add a new idea to the store.
        
        Args:
            idea: IdeaNode to add
            
        Raises:
            ValueError: If idea with same id already exists
        """
        if idea.id in self._ideas:
            raise ValueError(f"Idea with id '{idea.id}' already exists")
        
        self._ideas[idea.id] = idea
        self._save_idea_to_mongo(idea)
        self._save_data()
    
    def get_idea(self, idea_id: str) -> Optional[IdeaNode]:
        """
        Get an idea by id.
        
        Args:
            idea_id: ID of the idea to retrieve
            
        Returns:
            IdeaNode if found, None otherwise
        """
        return self._ideas.get(idea_id)
    
    def update_idea(self, idea: IdeaNode) -> None:
        """
        Update an existing idea.
        
        Args:
            idea: IdeaNode with updated data
            
        Raises:
            ValueError: If idea doesn't exist
        """
        if idea.id not in self._ideas:
            raise ValueError(f"Idea with id '{idea.id}' not found")
        
        from datetime import datetime
        idea.updated_at = datetime.now()
        self._ideas[idea.id] = idea
        self._save_idea_to_mongo(idea)
        self._save_data()
    
    def delete_idea(self, idea_id: str) -> None:
        """
        Delete an idea from the store.
        
        Args:
            idea_id: ID of the idea to delete
            
        Raises:
            ValueError: If idea doesn't exist
        """
        if idea_id not in self._ideas:
            raise ValueError(f"Idea with id '{idea_id}' not found")
        
        del self._ideas[idea_id]
        
        # Also remove any edges referencing this idea
        self._edges = [
            edge for edge in self._edges
            if edge.source_id != idea_id and edge.target_id != idea_id
        ]
        
        self._delete_idea_from_mongo(idea_id)
        self._delete_edges_from_mongo(idea_id)
        self._save_data()
    
    def get_all_ideas(self) -> List[IdeaNode]:
        """
        Get all ideas in the store.
        
        Returns:
            List of all IdeaNode instances
        """
        return list(self._ideas.values())
    
    def get_ideas_by_stage(self, stage: EvolutionStage) -> List[IdeaNode]:
        """
        Get all ideas at a specific evolution stage.
        
        Args:
            stage: EvolutionStage to filter by
            
        Returns:
            List of IdeaNode instances at the specified stage
        """
        return [
            idea for idea in self._ideas.values()
            if idea.stage == stage
        ]
    
    # Edge operations
    
    def add_edge(self, edge: InfluenceEdge) -> None:
        """
        Add a new influence edge to the store.
        
        Args:
            edge: InfluenceEdge to add
            
        Raises:
            ValueError: If source or target idea doesn't exist
        """
        # Validate that both ideas exist
        if edge.source_id not in self._ideas:
            raise ValueError(f"Source idea '{edge.source_id}' not found")
        
        if edge.target_id not in self._ideas:
            raise ValueError(f"Target idea '{edge.target_id}' not found")
        
        self._edges.append(edge)
        self._save_edge_to_mongo(edge)
        self._save_data()
    
    def get_edges_from(self, source_id: str) -> List[InfluenceEdge]:
        """
        Get all edges originating from a specific idea.
        
        Args:
            source_id: ID of the source idea
            
        Returns:
            List of InfluenceEdge instances
        """
        return [
            edge for edge in self._edges
            if edge.source_id == source_id
        ]
    
    def get_edges_to(self, target_id: str) -> List[InfluenceEdge]:
        """
        Get all edges pointing to a specific idea.
        
        Args:
            target_id: ID of the target idea
            
        Returns:
            List of InfluenceEdge instances
        """
        return [
            edge for edge in self._edges
            if edge.target_id == target_id
        ]
    
    def get_all_edges(self) -> List[InfluenceEdge]:
        """
        Get all edges in the store.
        
        Returns:
            List of all InfluenceEdge instances
        """
        return self._edges.copy()
    
    def delete_edge(self, source_id: str, target_id: str) -> None:
        """
        Delete an influence edge.
        
        Args:
            source_id: ID of the source idea
            target_id: ID of the target idea
            
        Raises:
            ValueError: If edge doesn't exist
        """
        original_length = len(self._edges)
        self._edges = [
            edge for edge in self._edges
            if not (edge.source_id == source_id and edge.target_id == target_id)
        ]
        
        if len(self._edges) == original_length:
            raise ValueError(
                f"Edge from '{source_id}' to '{target_id}' not found"
            )
        
        # Delete from MongoDB
        if self._mongo_connected:
            try:
                self._edges_collection.delete_one({
                    "source_id": source_id,
                    "target_id": target_id
                })
            except Exception as e:
                print(f"[WARN] MongoDB delete edge failed: {e}")
        
        self._save_data()
    
    # Utility methods
    
    def clear_all(self) -> None:
        """Clear all data from the store."""
        self._ideas.clear()
        self._edges.clear()
        
        if self._mongo_connected:
            try:
                self._ideas_collection.delete_many({})
                self._edges_collection.delete_many({})
            except Exception as e:
                print(f"[WARN] MongoDB clear failed: {e}")
        
        self._save_data()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the data store.
        
        Returns:
            Dictionary with counts of ideas and edges
        """
        return {
            'total_ideas': len(self._ideas),
            'total_edges': len(self._edges),
            'storage': 'MongoDB' if self._mongo_connected else 'JSON (fallback)',
            'ideas_by_stage': {
                stage.value: len(self.get_ideas_by_stage(stage))
                for stage in EvolutionStage
            }
        }
