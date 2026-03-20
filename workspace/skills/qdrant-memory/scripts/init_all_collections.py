#!/usr/bin/env python3
"""
Initialize Qdrant collections for Kimi Memory System
Creates 3 collections with mxbai-embed-large (1024 dims) using Qdrant 2025 best practices:

1. kimi_memories - Personal memories, preferences, lessons learned
2. kimi_kb - Knowledge base for web search, documents, scraped data
3. private_court_docs - Court documents and legal discussions

Features:
- on_disk=True for vectors (minimize RAM usage)
- on_disk_payload=True for payload
- Optimizer config for efficient indexing
- Binary quantization support (2025+ feature)

Usage: init_all_collections.py [--recreate]
"""

import argparse
import json
import os
import sys

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Collection configurations
COLLECTIONS = {
    "kimi_memories": {
        "description": "Personal memories, preferences, lessons learned",
        "vector_size": 1024
    },
    "kimi_kb": {
        "description": "Knowledge base - web data, documents, reference materials",
        "vector_size": 1024
    },
    "private_court_docs": {
        "description": "Court documents and legal discussions",
        "vector_size": 1024
    }
}

def make_request(url, data=None, method="GET"):
    """Make HTTP request with proper method"""
    import urllib.request
    req = urllib.request.Request(url, method=method)
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    if QDRANT_API_KEY:
        req.add_header("api-key", QDRANT_API_KEY)
    return req

def collection_exists(name):
    """Check if collection exists"""
    import urllib.request
    import urllib.error
    try:
        req = make_request(f"{QDRANT_URL}/collections/{name}")
        with urllib.request.urlopen(req, timeout=5) as response:
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise
    except Exception:
        return False

def get_collection_info(name):
    """Get collection info"""
    import urllib.request
    try:
        req = make_request(f"{QDRANT_URL}/collections/{name}")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return None

def create_collection(name, vector_size=1024):
    """Create a collection with Qdrant 2025 best practices"""
    import urllib.request
    
    config = {
        "vectors": {
            "size": vector_size,
            "distance": "Cosine",
            "on_disk": True,  # Store vectors on disk to minimize RAM
            "quantization_config": {
                "binary": {
                    "always_ram": True  # Keep compressed vectors in RAM for fast search
                }
            }
        },
        "on_disk_payload": True,  # Store payload on disk
        "shard_number": 1,  # Single node setup
        "replication_factor": 1,  # Single copy (set to 2 for production with HA)
        "optimizers_config": {
            "indexing_threshold": 20000,  # Start indexing after 20k points
            "default_segment_number": 0,  # Fewer/larger segments for better throughput
            "deleted_threshold": 0.2,  # Vacuum when 20% deleted
            "vacuum_min_vector_number": 1000  # Min vectors before vacuum
        }
    }
    
    req = make_request(
        f"{QDRANT_URL}/collections/{name}",
        data=config,
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get("result") == True
    except Exception as e:
        print(f"Error creating collection {name}: {e}", file=sys.stderr)
        return False

def delete_collection(name):
    """Delete a collection"""
    import urllib.request
    req = make_request(f"{QDRANT_URL}/collections/{name}", method="DELETE")
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            return result.get("status") == "ok"
    except Exception as e:
        print(f"Error deleting collection {name}: {e}", file=sys.stderr)
        return False

def main():
    import urllib.request
    
    parser = argparse.ArgumentParser(description="Initialize all Qdrant collections with 2025 best practices")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate all collections")
    parser.add_argument("--force", action="store_true", help="Force recreate even with existing data")
    args = parser.parse_args()
    
    # Check Qdrant connection
    try:
        req = urllib.request.Request(f"{QDRANT_URL}/")
        with urllib.request.urlopen(req, timeout=3) as response:
            pass
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant at {QDRANT_URL}: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Connected to Qdrant at {QDRANT_URL}\n")
    
    # Check if Ollama is available for embeddings
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as response:
            ollama_status = "✅"
    except Exception:
        ollama_status = "⚠️"
    
    print(f"Ollama (localhost): {ollama_status} - Embeddings endpoint\n")
    
    created = []
    skipped = []
    errors = []
    recreated = []
    
    for name, config in COLLECTIONS.items():
        print(f"--- {name} ---")
        print(f"  Description: {config['description']}")
        
        exists = collection_exists(name)
        
        if exists:
            info = get_collection_info(name)
            if info:
                actual_size = info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size", "?")
                points = info.get("result", {}).get("points_count", 0)
                on_disk = info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("on_disk", False)
                
                print(f"  ℹ️  Existing collection:")
                print(f"     Points: {points}")
                print(f"     Vector size: {actual_size}")
                print(f"     On disk: {on_disk}")
            
            if args.recreate:
                if points > 0 and not args.force:
                    print(f"  ⚠️  Collection has {points} points. Use --force to recreate with data loss.")
                    skipped.append(name)
                    continue
                
                print(f"  Deleting existing collection...")
                if delete_collection(name):
                    print(f"  ✅ Deleted")
                    exists = False
                else:
                    print(f"  ❌ Failed to delete", file=sys.stderr)
                    errors.append(name)
                    continue
            else:
                print(f"  ⚠️  Already exists, skipping (use --recreate to update)")
                skipped.append(name)
                continue
        
        if not exists:
            print(f"  Creating collection with 2025 best practices...")
            print(f"     - on_disk=True (vectors)")
            print(f"     - on_disk_payload=True")
            print(f"     - Binary quantization")
            print(f"     - Optimizer config")
            
            if create_collection(name, config["vector_size"]):
                print(f"  ✅ Created (vector size: {config['vector_size']})")
                if args.recreate and name in [c for c in COLLECTIONS]:
                    recreated.append(name)
                else:
                    created.append(name)
            else:
                print(f"  ❌ Failed to create", file=sys.stderr)
                errors.append(name)
        print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    if created:
        print(f"  Created: {', '.join(created)}")
    if recreated:
        print(f"  Recreated: {', '.join(recreated)}")
    if skipped:
        print(f"  Skipped: {', '.join(skipped)}")
    if errors:
        print(f"  Errors: {', '.join(errors)}")
        sys.exit(1)
    
    print("\n🎉 All collections ready with 2025 best practices!")
    print("\nCollections configured for mxbai-embed-large (1024 dims)")
    print("- kimi_memories: Personal memories (on_disk=True)")
    print("- kimi_kb: Knowledge base (on_disk=True)")
    print("- private_court_docs: Court documents (on_disk=True)")
    print("\nFeatures enabled:")
    print("  ✓ Vectors stored on disk (minimizes RAM)")
    print("  ✓ Payload stored on disk")
    print("  ✓ Binary quantization for fast search")
    print("  ✓ Optimized indexing thresholds")

if __name__ == "__main__":
    main()
