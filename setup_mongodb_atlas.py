#!/usr/bin/env python3
"""
MongoDB Atlas Setup Helper Script

This script helps you configure MongoDB Atlas for the Yugas Evolution application.
It will guide you through the setup process and test your connection.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(number, text):
    """Print a numbered step."""
    print(f"[{number}] {text}")

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def get_input(prompt, default=None):
    """Get user input with optional default."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else default

def test_connection(uri, db_name, collection_name):
    """Test MongoDB Atlas connection."""
    try:
        from pymongo import MongoClient
        
        print_info("Testing connection...")
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.server_info()
        
        db = client[db_name]
        collection = db[collection_name]
        
        # Try to insert a test document
        test_doc = {"test": "connection", "timestamp": __import__('datetime').datetime.now()}
        result = collection.insert_one(test_doc)
        
        # Clean up
        collection.delete_one({"_id": result.inserted_id})
        
        print_success("Connection successful!")
        
        # Show stats
        stats = {
            "database": db_name,
            "collection": collection_name,
            "total_documents": collection.count_documents({})
        }
        
        print_info(f"Database: {stats['database']}")
        print_info(f"Collection: {stats['collection']}")
        print_info(f"Total documents: {stats['total_documents']}")
        
        return True
        
    except ImportError:
        print_error("pymongo is not installed!")
        print_info("Install it with: pip install pymongo")
        return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False

def main():
    """Main setup flow."""
    print_header("MongoDB Atlas Setup for Yugas Evolution")
    
    print("This script will help you configure MongoDB Atlas as your database backend.")
    print("You'll need:")
    print("  • A MongoDB Atlas account (free at mongodb.com/cloud/atlas)")
    print("  • Your connection string from Atlas")
    print("  • Your database username and password")
    
    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv()
        print_info(".env file found")
    else:
        print_info(".env file not found, will create one")
    
    # Get connection details
    print_header("Step 1: Connection String")
    print("You can find your connection string in MongoDB Atlas:")
    print("  1. Go to Databases")
    print("  2. Click 'Connect' on your cluster")
    print("  3. Choose 'Drivers' → 'Python'")
    print("  4. Copy the connection string")
    print()
    
    uri = get_input(
        "Enter your MongoDB Atlas connection string",
        os.getenv("MONGODB_ATLAS_URI", "")
    )
    
    if not uri:
        print_error("Connection string is required!")
        return False
    
    if "mongodb+srv://" not in uri:
        print_error("Invalid connection string format. Should start with 'mongodb+srv://'")
        return False
    
    print_success("Connection string saved")
    
    # Get database name
    print_header("Step 2: Database Configuration")
    db_name = get_input(
        "Enter database name",
        os.getenv("MONGODB_DATABASE", "yuga_evolution_db")
    )
    
    collection_name = get_input(
        "Enter collection name",
        os.getenv("MONGODB_COLLECTION", "ideas")
    )
    
    print_success("Database configuration saved")
    
    # Test connection
    print_header("Step 3: Testing Connection")
    if not test_connection(uri, db_name, collection_name):
        print_error("Connection test failed!")
        print_info("Please check your connection string and try again.")
        return False
    
    # Save to .env
    print_header("Step 4: Saving Configuration")
    
    set_key(str(env_path), "MONGODB_ATLAS_URI", uri)
    set_key(str(env_path), "MONGODB_DATABASE", db_name)
    set_key(str(env_path), "MONGODB_COLLECTION", collection_name)
    
    print_success(".env file updated with MongoDB Atlas configuration")
    
    # Install pymongo if needed
    print_header("Step 5: Installing Dependencies")
    try:
        import pymongo
        print_success("pymongo is already installed")
    except ImportError:
        print_info("Installing pymongo...")
        os.system("pip install pymongo")
    
    # Final summary
    print_header("Setup Complete! 🎉")
    print("Your MongoDB Atlas configuration is ready!")
    print()
    print("Next steps:")
    print("  1. Start the application: start.bat")
    print("  2. Open http://localhost:8080/yugas")
    print("  3. Create and explore ideas")
    print()
    print("Your data will now be stored in MongoDB Atlas!")
    print()
    print("To monitor your database:")
    print("  • Go to MongoDB Atlas dashboard")
    print("  • Click 'Databases' → 'Browse Collections'")
    print("  • Navigate to your database and collection")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
