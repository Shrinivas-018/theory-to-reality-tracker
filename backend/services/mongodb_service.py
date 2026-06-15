"""
MongoDB Service for Yuga Evolution Storage

Handles connection and operations with MongoDB for storing Yuga evolution data.
Supports both local MongoDB and MongoDB Atlas.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
import time
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Session cache: token -> {"user": user_dict, "expires": timestamp}
_session_cache = {}
_SESSION_CACHE_TTL = 60  # seconds


class MongoDBService:
    """Service for MongoDB operations with Atlas support."""
    
    def __init__(self, connection_string: str = None):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string. If None, will try to load from environment.
                             Supports both local MongoDB and MongoDB Atlas URIs.
        """
        # Try to get connection string from environment first
        if connection_string is None:
            connection_string = os.getenv(
                "MONGODB_ATLAS_URI",
                os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            )
        
        self.connection_string = connection_string
        self.db_name = os.getenv("MONGODB_DATABASE", "yuga_evolution_db")
        self.collection_name = os.getenv("MONGODB_COLLECTION", "ideas")
        self.client = None
        self.db = None
        self.collection = None
        self._connected = False
        self._indexes_created = False
        self._is_atlas = "mongodb+srv://" in connection_string
        
        # Try to import pymongo
        try:
            from pymongo import MongoClient
            self.MongoClient = MongoClient
            # Don't connect immediately - do it lazily on first use
        except ImportError:
            print("Warning: pymongo not installed. MongoDB features will use fallback storage.")
            self.MongoClient = None
    
    def _ensure_connected(self):
        """Ensure connection is established (lazy connection)."""
        if not self._connected and self.MongoClient:
            self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB or MongoDB Atlas."""
        if not self.MongoClient:
            return False
            
        try:
            # Set appropriate timeout based on connection type
            timeout_ms = 30000 if self._is_atlas else 5000
            
            # For MongoDB Atlas, disable SSL verification if having issues
            connection_params = {
                "serverSelectionTimeoutMS": timeout_ms,
                "connectTimeoutMS": timeout_ms,
                "retryWrites": True,
                "maxPoolSize": 50,
                "minPoolSize": 10,
            }
            
            # Add SSL options for Atlas - use only tlsInsecure
            if self._is_atlas:
                connection_params["ssl"] = True
                connection_params["tlsInsecure"] = True
            
            self.client = self.MongoClient(
                self.connection_string,
                **connection_params
            )
            
            # Test connection with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.client.server_info()
                    break
                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        print(f"  Connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(2)
                    else:
                        raise retry_error
            
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.users_collection = self.db["users"]
            self.sessions_collection = self.db["sessions"]
            self.search_history_collection = self.db["search_history"]
            self.chat_history_collection = self.db["chat_history"]
            
            # Create indexes for better performance (only once)
            if not self._indexes_created:
                self._create_indexes()
                self._indexes_created = True
            
            self._connected = True
            connection_type = "MongoDB Atlas" if self._is_atlas else "Local MongoDB"
            print(f"[OK] Connected to {connection_type}: {self.db_name}")
            
            # Auto-seed from JSON fallback if MongoDB is empty
            self._auto_seed_from_fallback()
            
            return True
        except Exception as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            print("  Using fallback JSON storage instead.")
            self._connected = False
            return False
    
    def _create_indexes(self):
        """Create indexes for better query performance."""
        try:
            # Drop old single-field unique index if it exists to allow per-user isolation
            try:
                self.collection.drop_index("idea_1")
            except Exception:
                pass
                
            # Compound unique index on (idea, user_id) to isolate ideas per user
            self.collection.create_index([("idea", 1), ("user_id", 1)], unique=True)
            # Index on timestamp for sorting
            self.collection.create_index("timestamp")
            # Index on category for filtering
            self.collection.create_index("category")
            
            # User collection indexes
            self.users_collection.create_index("username", unique=True)
            
            # Sessions indexes (TTL index to auto-delete expired sessions is a fantastic addition!)
            self.sessions_collection.create_index("token", unique=True)
            self.sessions_collection.create_index("expires_at", expireAfterSeconds=0)
            
            # Search history indexes
            self.search_history_collection.create_index([("user_id", 1), ("timestamp", -1)])
            
            # Chat history indexes — compound index for fast lookup per user+idea
            self.chat_history_collection.create_index([("user_id", 1), ("idea_id", 1)])
            self.chat_history_collection.create_index([("user_id", 1), ("idea_id", 1), ("timestamp", 1)])
            
            print("[OK] Database indexes created (users, sessions, search history, chat history, isolated ideas)")
        except Exception as e:
            print(f"[WARNING] Could not create indexes: {e}")
    
    def _auto_seed_from_fallback(self):
        """If MongoDB collection is empty but fallback JSON has data, seed MongoDB."""
        if not self._connected:
            return
        try:
            count = self.collection.count_documents({})
            if count > 0:
                return  # Already has data
            
            # Check for fallback data
            from pathlib import Path
            fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
            if not fallback_file.exists():
                return
            
            with open(fallback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                return
            
            print(f"[INFO] Seeding MongoDB with {len(data)} ideas from fallback JSON...")
            inserted = 0
            for record in data:
                try:
                    self.collection.replace_one(
                        {"idea": record["idea"]},
                        record,
                        upsert=True
                    )
                    inserted += 1
                except Exception:
                    pass
            print(f"[OK] Seeded {inserted} ideas into MongoDB")
        except Exception as e:
            print(f"[WARN] Auto-seed failed: {e}")
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        self._ensure_connected()
        return self._connected
    
    def get_connection_info(self) -> Dict:
        """Get information about the current connection."""
        self._ensure_connected()
        return {
            "connected": self._connected,
            "type": "MongoDB Atlas" if self._is_atlas else "Local MongoDB",
            "database": self.db_name,
            "collection": self.collection_name,
            "uri_masked": self.connection_string[:50] + "..." if len(self.connection_string) > 50 else self.connection_string
        }
    
    def insert_idea(self, idea_record: Dict, user_id: str = None) -> Optional[str]:
        """
        Insert or update a Yuga evolution record in MongoDB.
        If a record with the same idea name already exists for this user, it is replaced
        with the new content (upsert). Returns the document ID.
        """
        self._ensure_connected()
        
        if not self._connected:
            return self._fallback_insert(idea_record, user_id)

        try:
            # Use a copy so pymongo's _id injection doesn't mutate the caller's dict
            doc = dict(idea_record)
            if user_id:
                doc["user_id"] = user_id
            else:
                doc.pop("user_id", None)
                
            # Filter by both idea and user_id to ensure absolute data isolation
            query = {"idea": idea_record["idea"]}
            if user_id:
                query["user_id"] = user_id
            else:
                query["user_id"] = {"$exists": False}
                
            result = self.collection.replace_one(
                query,                           # filter
                doc,                             # replacement
                upsert=True                      # insert if not found
            )
            
            if result.upserted_id:
                doc_id = str(result.upserted_id)
                print(f"[OK] Inserted: {idea_record['idea']} (ID: {doc_id}) [User: {user_id}]")
            else:
                # Updated existing — fetch the _id
                existing = self.collection.find_one(query, {"_id": 1})
                doc_id = str(existing["_id"]) if existing else idea_record["idea"]
                print(f"[OK] Updated: {idea_record['idea']} (ID: {doc_id}) [User: {user_id}]")
            return doc_id

        except Exception as e:
            print(f"[ERROR] Error upserting {idea_record['idea']}: {e}")
            return self._fallback_insert(idea_record, user_id)
    
    def _fallback_insert(self, idea_record: Dict, user_id: str = None) -> Optional[str]:
        """Fallback upsert to JSON file when MongoDB is unavailable."""
        from pathlib import Path

        fallback_dir = Path("data/yuga_evolution_fallback")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fallback_file = fallback_dir / "ideas.json"

        if fallback_file.exists():
            with open(fallback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []

        doc = dict(idea_record)
        if user_id:
            doc["user_id"] = user_id

        # Replace existing entry if found, otherwise append
        replaced = False
        for i, item in enumerate(data):
            match_idea = item.get("idea") == idea_record["idea"]
            match_user = item.get("user_id") == user_id if user_id else "user_id" not in item
            if match_idea and match_user:
                data[i] = doc
                replaced = True
                print(f"[OK] Updated in fallback: {idea_record['idea']} [User: {user_id}]")
                break

        if not replaced:
            data.append(doc)
            print(f"[OK] Inserted to fallback: {idea_record['idea']} [User: {user_id}]")

        with open(fallback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return idea_record["idea"]
    
    def get_all_ideas(self, limit: int = 100, user_id: str = None) -> List[Dict]:
        """
        Retrieve all Yuga evolution records.
        
        Args:
            limit: Maximum number of records to return
            user_id: ID of the user to isolate search records
            
        Returns:
            List of idea records
        """
        self._ensure_connected()
        
        if not self._connected:
            return self._fallback_get_all(limit, user_id)
        
        try:
            query = {}
            if user_id:
                query["user_id"] = user_id
            else:
                query["user_id"] = {"$exists": False}
                
            cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
            ideas = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                ideas.append(doc)
            return ideas
        except Exception as e:
            print(f"Error retrieving ideas: {e}")
            return self._fallback_get_all(limit, user_id)
    
    def _fallback_get_all(self, limit: int = 100, user_id: str = None) -> List[Dict]:
        """Fallback retrieval from JSON file."""
        from pathlib import Path
        
        fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
        
        if not fallback_file.exists():
            return []
        
        try:
            with open(fallback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Filter fallback by user_id
            filtered = []
            for doc in data:
                match_user = doc.get("user_id") == user_id if user_id else "user_id" not in doc
                if match_user:
                    filtered.append(doc)
                    
            return filtered[:limit]
        except Exception as e:
            print(f"Error reading fallback data: {e}")
            return []
    
    def get_idea_by_name(self, idea_name: str, user_id: str = None) -> Optional[Dict]:
        """Get a specific idea by name."""
        self._ensure_connected()
        
        if not self._connected:
            return self._fallback_get_by_name(idea_name, user_id)
        
        try:
            query = {"idea": idea_name}
            if user_id:
                query["user_id"] = user_id
            else:
                query["user_id"] = {"$exists": False}
                
            doc = self.collection.find_one(query)
            if doc:
                doc['_id'] = str(doc['_id'])
            return doc
        except Exception as e:
            print(f"Error retrieving idea: {e}")
            return self._fallback_get_by_name(idea_name, user_id)
    
    def _fallback_get_by_name(self, idea_name: str, user_id: str = None) -> Optional[Dict]:
        """Fallback retrieval by name from JSON."""
        all_ideas = self._fallback_get_all(limit=10000, user_id=user_id)
        for idea in all_ideas:
            if idea["idea"] == idea_name:
                return idea
        return None
    
    def delete_idea(self, idea_name: str, user_id: str = None) -> bool:
        """Delete an idea by name."""
        self._ensure_connected()
        
        if not self._connected:
            return self._fallback_delete(idea_name, user_id)
        
        try:
            query = {"idea": idea_name}
            if user_id:
                query["user_id"] = user_id
            else:
                query["user_id"] = {"$exists": False}
                
            result = self.collection.delete_one(query)
            if result.deleted_count > 0:
                print(f"[OK] Deleted: {idea_name} [User: {user_id}]")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Error deleting {idea_name}: {e}")
            return False
    
    def _fallback_delete(self, idea_name: str, user_id: str = None) -> bool:
        """Fallback delete from JSON."""
        from pathlib import Path
        fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
        if not fallback_file.exists():
            return False
        
        with open(fallback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_len = len(data)
        
        # Keep ideas that are not matching both name and user
        new_data = []
        for item in data:
            match_idea = item.get("idea") == idea_name
            match_user = item.get("user_id") == user_id if user_id else "user_id" not in item
            if not (match_idea and match_user):
                new_data.append(item)
                
        if len(new_data) == original_len:
            return False
        
        with open(fallback_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, default=str)
        
        return True
    
    def update_idea(self, idea_name: str, updates: Dict, user_id: str = None) -> bool:
        """Update specific fields of an idea."""
        self._ensure_connected()
        
        if not self._connected:
            return self._fallback_update(idea_name, updates, user_id)
        
        try:
            query = {"idea": idea_name}
            if user_id:
                query["user_id"] = user_id
            else:
                query["user_id"] = {"$exists": False}
                
            result = self.collection.update_one(
                query,
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[ERROR] Error updating {idea_name}: {e}")
            return False
    
    def _fallback_update(self, idea_name: str, updates: Dict, user_id: str = None) -> bool:
        """Fallback update in JSON."""
        from pathlib import Path
        fallback_file = Path("data/yuga_evolution_fallback/ideas.json")
        if not fallback_file.exists():
            return False
        
        with open(fallback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated = False
        for item in data:
            match_idea = item.get("idea") == idea_name
            match_user = item.get("user_id") == user_id if user_id else "user_id" not in item
            if match_idea and match_user:
                item.update(updates)
                updated = True
                break
        
        if updated:
            with open(fallback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        return updated
    
    def get_stats(self, user_id: str = None) -> Dict:
        """Get statistics about stored ideas."""
        self._ensure_connected()
        
        if not self._connected:
            all_ideas = self._fallback_get_all(limit=10000, user_id=user_id)
            return {
                "total_ideas": len(all_ideas),
                "storage": "JSON fallback",
                "database": "File system",
                "connection_type": "None"
            }
        
        try:
            query = {}
            if user_id:
                query["user_id"] = user_id
            else:
                query["user_id"] = {"$exists": False}
                
            total = self.collection.count_documents(query)
            connection_type = "MongoDB Atlas" if self._is_atlas else "Local MongoDB"
            return {
                "total_ideas": total,
                "storage": "MongoDB",
                "database": self.db_name,
                "collection": self.collection_name,
                "connection_type": connection_type
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total_ideas": 0, "storage": "Unknown"}
    
    def export_to_csv(self, output_file: str = "yuga_evolution_export.csv", user_id: str = None) -> bool:
        """Export user's ideas to CSV format."""
        import csv
        
        ideas = self.get_all_ideas(limit=10000, user_id=user_id)
        
        if not ideas:
            print("No ideas to export")
            return False
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    "Idea", "Description", "Source",
                    "Satya Yuga", "Treta Yuga", "Dwapar Yuga", "Kali Yuga",
                    "Timestamp"
                ])
                
                # Data rows
                for idea in ideas:
                    evolution = idea.get("evolution", {})
                    writer.writerow([
                        idea.get("idea", ""),
                        idea.get("description", ""),
                        idea.get("source", ""),
                        json.dumps(evolution.get("satya_yuga", {})),
                        json.dumps(evolution.get("treta_yuga", {})),
                        json.dumps(evolution.get("dwapar_yuga", {})),
                        json.dumps(evolution.get("kali_yuga", {})),
                        idea.get("timestamp", "")
                    ])
            
            print(f"[OK] Exported {len(ideas)} ideas to {output_file} [User: {user_id}]")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error exporting to CSV: {e}")
            return False

    # ─── User Management & Auth operations ─────────────────────────
    
    def register_user(self, username: str, password_hash: str) -> Dict:
        """Register a new user in the database."""
        self._ensure_connected()
        if not self._connected:
            return {"username": username, "id": username, "created_at": datetime.now()}
            
        doc = {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.now()
        }
        self.users_collection.insert_one(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc
        
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Find a user by username."""
        self._ensure_connected()
        if not self._connected:
            return None
        doc = self.users_collection.find_one({"username": username})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc
        
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Find a user by string ID."""
        self._ensure_connected()
        if not self._connected:
            return None
        from bson import ObjectId
        try:
            doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        except Exception:
            return None
            
    def create_session(self, user_id: str) -> str:
        """Create a secure session token for a user."""
        self._ensure_connected()
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(days=7)
        
        if self._connected:
            try:
                self.sessions_collection.insert_one({
                    "token": token,
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "expires_at": expires_at
                })
            except Exception as e:
                print(f"[ERROR] Failed to save session: {e}")
        return token
        
    def get_user_from_session(self, token: str) -> Optional[Dict]:
        """Verify session token and retrieve corresponding user.
        Uses in-memory cache to avoid hitting MongoDB on every request."""
        # Check cache first
        cached = _session_cache.get(token)
        if cached and time.time() < cached["expires"]:
            return cached["user"]
        
        self._ensure_connected()
        if not self._connected:
            return None
            
        session = self.sessions_collection.find_one({"token": token})
        if not session:
            _session_cache.pop(token, None)
            return None
            
        # Double check expiration (TTL index handles this, but extra check is robust)
        if session.get("expires_at") and session["expires_at"] < datetime.now():
            self.sessions_collection.delete_one({"token": token})
            _session_cache.pop(token, None)
            return None
            
        user = self.get_user_by_id(session["user_id"])
        if user:
            _session_cache[token] = {"user": user, "expires": time.time() + _SESSION_CACHE_TTL}
        return user
        
    def delete_session(self, token: str) -> bool:
        """Revoke a session (logout)."""
        _session_cache.pop(token, None)  # Clear from cache
        self._ensure_connected()
        if not self._connected:
            return True
        result = self.sessions_collection.delete_one({"token": token})
        return result.deleted_count > 0
        
    # ─── Search History operations ──────────────────────────────────
    
    def log_search(self, user_id: str, query: str, search_type: str, results_count: int) -> None:
        """Record a search query inside search_history collection."""
        self._ensure_connected()
        if not self._connected:
            return
            
        try:
            self.search_history_collection.insert_one({
                "user_id": user_id,
                "query": query.strip(),
                "search_type": search_type,
                "results_count": results_count,
                "timestamp": datetime.now()
            })
        except Exception as e:
            print(f"[WARN] Failed to log search history: {e}")
            
    def get_search_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get past searches for a user sorted by timestamp descending."""
        self._ensure_connected()
        if not self._connected:
            return []
            
        try:
            cursor = self.search_history_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
            history = []
            for doc in cursor:
                history.append({
                    "id": str(doc["_id"]),
                    "query": doc.get("query", ""),
                    "search_type": doc.get("search_type", "basic"),
                    "results_count": doc.get("results_count", 0),
                    "timestamp": doc.get("timestamp").isoformat() if doc.get("timestamp") else ""
                })
            return history
        except Exception as e:
            print(f"[ERROR] Failed to get search history: {e}")
            return []

    # ─── Chat History operations ────────────────────────────────────

    def save_chat_message(self, user_id: str, idea_id: str, role: str, content: str) -> Optional[str]:
        """Save a single chat message to the chat_history collection."""
        self._ensure_connected()
        if not self._connected:
            return None

        try:
            doc = {
                "user_id": user_id,
                "idea_id": idea_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
            }
            result = self.chat_history_collection.insert_one(doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"[WARN] Failed to save chat message: {e}")
            return None

    def get_chat_history(self, user_id: str, idea_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve chat history for a specific user and idea, sorted chronologically."""
        self._ensure_connected()
        if not self._connected:
            return []

        try:
            cursor = self.chat_history_collection.find(
                {"user_id": user_id, "idea_id": idea_id}
            ).sort("timestamp", 1).limit(limit)

            messages = []
            for doc in cursor:
                messages.append({
                    "id": str(doc["_id"]),
                    "role": doc.get("role", "user"),
                    "content": doc.get("content", ""),
                    "timestamp": doc.get("timestamp").isoformat() if doc.get("timestamp") else "",
                })
            return messages
        except Exception as e:
            print(f"[ERROR] Failed to get chat history: {e}")
            return []

    def clear_chat_history(self, user_id: str, idea_id: str) -> bool:
        """Delete all chat messages for a specific user and idea."""
        self._ensure_connected()
        if not self._connected:
            return False

        try:
            result = self.chat_history_collection.delete_many(
                {"user_id": user_id, "idea_id": idea_id}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"[ERROR] Failed to clear chat history: {e}")
            return False
