"""Quick diagnostic script to check edge data integrity."""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "evolution_tracker_api")

with open(os.path.join(DATA_DIR, "edges.json"), "r") as f:
    edges = json.load(f)

with open(os.path.join(DATA_DIR, "ideas.json"), "r") as f:
    ideas = json.load(f)

idea_ids = set(ideas.keys())
print(f"Total ideas: {len(idea_ids)}")
print(f"Total edges in file: {len(edges)}")

bad = []
for e in edges:
    src = e.get("source_id", "")
    tgt = e.get("target_id", "")
    if src not in idea_ids or tgt not in idea_ids:
        bad.append(e)

print(f"Edges with missing nodes: {len(bad)}")
for e in bad[:10]:
    src_ok = e["source_id"] in idea_ids
    tgt_ok = e["target_id"] in idea_ids
    print(f"  src={e['source_id']} (exists={src_ok}), tgt={e['target_id']} (exists={tgt_ok})")

# Check for duplicate idea add_idea issues
from backend.models import IdeaNode
from backend.services import LineageGraph

graph = LineageGraph()
dup_count = 0
for idea_id, idea_data in ideas.items():
    try:
        idea = IdeaNode.from_dict(idea_data)
        graph.add_idea(idea)
    except ValueError:
        dup_count += 1

print(f"\nDuplicate idea additions: {dup_count}")
print(f"Graph nodes after add: {graph.node_count}")

# Try adding edges
edge_ok = 0
edge_fail = 0
first_err = None
from backend.models import InfluenceEdge
for e in edges:
    try:
        edge = InfluenceEdge.from_dict(e)
        graph.add_influence(edge)
        edge_ok += 1
    except Exception as ex:
        edge_fail += 1
        if first_err is None:
            first_err = str(ex)

print(f"Edges loaded OK: {edge_ok}")
print(f"Edges failed: {edge_fail}")
if first_err:
    print(f"First error: {first_err}")
