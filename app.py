from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import networkx as nx

app = Flask(__name__)
CORS(app)

# Load dataset - fall back to sample data if CSV missing
import os
CSV_PATH = "data/clean_nobel.csv"
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    # Sample data so the app still runs
    df = pd.DataFrame([
        {"laureate": "Albert Einstein", "category": "Physics", "year": 1921, "motivation": "Discovery of the photoelectric effect"},
        {"laureate": "Marie Curie", "category": "Physics", "year": 1903, "motivation": "Research on radiation phenomena"},
        {"laureate": "Marie Curie", "category": "Chemistry", "year": 1911, "motivation": "Discovery of radium and polonium"},
        {"laureate": "Richard Feynman", "category": "Physics", "year": 1965, "motivation": "Fundamental work in quantum electrodynamics"},
        {"laureate": "Werner Heisenberg", "category": "Physics", "year": 1932, "motivation": "Creation of quantum mechanics"},
        {"laureate": "Niels Bohr", "category": "Physics", "year": 1922, "motivation": "Investigation of atomic structure"},
        {"laureate": "Ernest Rutherford", "category": "Chemistry", "year": 1908, "motivation": "Investigations into disintegration of elements"},
        {"laureate": "Linus Pauling", "category": "Chemistry", "year": 1954, "motivation": "Research into chemical bonds"},
        {"laureate": "Alexander Fleming", "category": "Medicine", "year": 1945, "motivation": "Discovery of penicillin"},
        {"laureate": "Francis Crick", "category": "Medicine", "year": 1962, "motivation": "Discoveries concerning molecular structure of DNA"},
        {"laureate": "James Watson", "category": "Medicine", "year": 1962, "motivation": "Discoveries concerning molecular structure of DNA"},
        {"laureate": "Ivan Pavlov", "category": "Medicine", "year": 1904, "motivation": "Work on physiology of digestion"},
        {"laureate": "Martin Luther King Jr.", "category": "Peace", "year": 1964, "motivation": "Non-violent struggle for civil rights"},
        {"laureate": "Malala Yousafzai", "category": "Peace", "year": 2014, "motivation": "Struggle against suppression of children and for right to education"},
        {"laureate": "Paul Samuelson", "category": "Economics", "year": 1970, "motivation": "Scientific work developing static and dynamic economic theory"},
        {"laureate": "Milton Friedman", "category": "Economics", "year": 1976, "motivation": "Achievements in consumption analysis and monetary history"},
    ])

@app.route("/")
def home():
    return jsonify({
        "message": "Nobel API running",
        "endpoints": ["/laureates", "/search?name=Einstein", "/categories", "/stats", "/connections"]
    })

@app.route("/laureates")
def laureates():
    category = request.args.get("category", "")
    if category:
        result = df[df["category"] == category]
    else:
        result = df
    return jsonify(result.to_dict(orient="records"))

@app.route("/search")
def search():
    name = request.args.get("name", "")
    results = df[df["laureate"].str.contains(name, case=False, na=False)]
    return jsonify(results.to_dict(orient="records"))

@app.route("/categories")
def categories():
    return jsonify(df["category"].unique().tolist())

@app.route("/stats")
def stats():
    return jsonify({
        "total_laureates": len(df),
        "categories": df["category"].nunique(),
        "earliest_year": int(df["year"].min()),
        "latest_year": int(df["year"].max())
    })

@app.route("/connections")
def connections():
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_node(row["laureate"], year=row["year"], category=row["category"])
    grouped = df.groupby(["year", "category"])
    for _, group in grouped:
        names = group["laureate"].tolist()
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                G.add_edge(names[i], names[j])
    nodes = [{"id": n, "label": n} for n in G.nodes()]
    edges = [{"source": e[0], "target": e[1]} for e in G.edges()]
    return jsonify({"nodes": nodes, "edges": edges})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
