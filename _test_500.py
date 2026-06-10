"""Reproduce the 500 error by simulating what the endpoint does."""
import json
from flask import Flask
from backend.services.yuga_generator import YugaGeneratorService

app = Flask(__name__)

g = YugaGeneratorService()

# Simulate what the endpoint does
record = g.create_yuga_record("cricket", "", "Manual")

print("Record keys:", list(record.keys()))
print("Images:", record.get("images"))
print("created_at type:", type(record.get("created_at")))
print("timestamp type:", type(record.get("timestamp")))

# Try jsonify
with app.app_context():
    from flask import jsonify
    try:
        resp = jsonify({"status": "success", "data": record})
        print("jsonify OK")
    except Exception as e:
        print(f"jsonify FAILED: {e}")

# Also check evolution structure
for yuga, data in record["evolution"].items():
    for key, val in data.items():
        if not isinstance(val, (str, list, dict, int, float, bool, type(None))):
            print(f"BAD TYPE in {yuga}.{key}: {type(val)} = {val}")
