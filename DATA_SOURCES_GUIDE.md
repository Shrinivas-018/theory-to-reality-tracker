# Dataset Sources Guide - Evolution Tracker

Complete guide for obtaining real scholarly data for your Evolution Tracker application.

---

## 🎯 Quick Start - Use Existing Script

You already have a working OpenAlex fetcher! Just run:

```bash
python backend/scripts/fetch_openalex.py
```

This will:
- ✅ Fetch 200 top concepts from OpenAlex (free, no API key needed)
- ✅ Get real author names for each concept
- ✅ Generate evolution chains based on concept relationships
- ✅ Create ~200 ideas with ~500+ edges
- ✅ Save to `data/evolution_tracker_api/`

**Then restart your backend:**
```bash
python -m backend.api
```

---

## 📚 Data Source Options

### 1. **OpenAlex** (Recommended - Already Implemented) ⭐

**What it is:** Free, open scholarly database with 250M+ works, concepts, authors, and institutions.

**Pros:**
- ✅ Completely free, no API key required
- ✅ Massive dataset (250M+ scholarly works)
- ✅ Real author names and citations
- ✅ Concept hierarchies and relationships
- ✅ Already implemented in your project!

**Cons:**
- ⚠️ Rate limited (10 requests/second)
- ⚠️ Concept relationships are broad (not evolution-specific)

**How to use:**
```bash
# Fetch 200 top concepts
python backend/scripts/fetch_openalex.py

# Customize the fetch (edit the script):
# - Change per-page parameter (max 200)
# - Filter by specific fields
# - Adjust concept levels
```

**API Documentation:** https://docs.openalex.org/

**Example queries:**
```python
# Top concepts by citation count
https://api.openalex.org/concepts?per-page=200&sort=cited_by_count:desc

# Concepts in specific field
https://api.openalex.org/concepts?filter=level:0&search=physics

# Works for a concept
https://api.openalex.org/works?filter=concepts.id:C41008148&per-page=100
```

---

### 2. **Semantic Scholar** (Alternative)

**What it is:** Free academic search engine with 200M+ papers and citation graphs.

**Pros:**
- ✅ Free API with generous limits
- ✅ Rich citation data
- ✅ Paper abstracts and metadata
- ✅ Author influence scores

**Cons:**
- ⚠️ Requires API key (free but needs registration)
- ⚠️ No built-in concept hierarchies

**How to use:**

1. **Get API Key:** https://www.semanticscholar.org/product/api

2. **Create fetcher script:**
```python
import requests

API_KEY = "your_api_key_here"
headers = {"x-api-key": API_KEY}

# Search papers
url = "https://api.semanticscholar.org/graph/v1/paper/search"
params = {
    "query": "machine learning",
    "fields": "title,abstract,authors,citationCount,year",
    "limit": 100
}
response = requests.get(url, params=params, headers=headers)
papers = response.json()["data"]

# Get paper details with citations
paper_id = papers[0]["paperId"]
url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
params = {"fields": "title,authors,citations,references"}
response = requests.get(url, params=params, headers=headers)
```

**API Documentation:** https://api.semanticscholar.org/api-docs/

---

### 3. **arXiv** (For Recent Research)

**What it is:** Open-access repository of 2M+ preprints in physics, math, CS, etc.

**Pros:**
- ✅ Completely free, no API key
- ✅ Full-text papers available
- ✅ Recent cutting-edge research
- ✅ Well-structured metadata

**Cons:**
- ⚠️ No citation data
- ⚠️ Limited to preprints (not peer-reviewed)
- ⚠️ No concept hierarchies

**How to use:**

```python
import urllib.request
import xml.etree.ElementTree as ET

# Search arXiv
query = "machine+learning"
url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=100"

response = urllib.request.urlopen(url)
xml_data = response.read()
root = ET.fromstring(xml_data)

# Parse entries
for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
    title = entry.find('{http://www.w3.org/2005/Atom}title').text
    authors = [a.find('{http://www.w3.org/2005/Atom}name').text 
               for a in entry.findall('{http://www.w3.org/2005/Atom}author')]
    published = entry.find('{http://www.w3.org/2005/Atom}published').text
    print(f"{title} by {authors} ({published})")
```

**API Documentation:** https://info.arxiv.org/help/api/index.html

---

### 4. **CrossRef** (For DOI Metadata)

**What it is:** Official DOI registration agency with metadata for 140M+ scholarly works.

**Pros:**
- ✅ Free, no API key required
- ✅ Comprehensive metadata
- ✅ Citation data available
- ✅ Publisher information

**Cons:**
- ⚠️ Rate limited (50 requests/second with polite pool)
- ⚠️ No concept hierarchies
- ⚠️ Requires DOIs to query

**How to use:**

```python
import requests

# Search works
url = "https://api.crossref.org/works"
params = {
    "query": "quantum computing",
    "rows": 100,
    "mailto": "your@email.com"  # Polite pool for better rate limits
}
response = requests.get(url, params=params)
works = response.json()["message"]["items"]

# Get specific work by DOI
doi = "10.1038/nature12373"
url = f"https://api.crossref.org/works/{doi}"
response = requests.get(url)
work = response.json()["message"]
```

**API Documentation:** https://api.crossref.org/

---

### 5. **PubMed/PMC** (For Biomedical Research)

**What it is:** Free database of 35M+ biomedical literature citations.

**Pros:**
- ✅ Free, no API key required
- ✅ Comprehensive biomedical coverage
- ✅ MeSH term hierarchies
- ✅ Full-text articles in PMC

**Cons:**
- ⚠️ Limited to biomedical fields
- ⚠️ Rate limited (3 requests/second)
- ⚠️ XML-based API (more complex)

**How to use:**

```python
import urllib.request
import xml.etree.ElementTree as ET

# Search PubMed
query = "CRISPR"
url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=100"
response = urllib.request.urlopen(url)
xml_data = response.read()
root = ET.fromstring(xml_data)
pmids = [id_elem.text for id_elem in root.findall('.//Id')]

# Fetch article details
pmid_list = ",".join(pmids[:10])
url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid_list}&retmode=xml"
response = urllib.request.urlopen(url)
articles_xml = response.read()
```

**API Documentation:** https://www.ncbi.nlm.nih.gov/books/NBK25501/

---

### 6. **Wikipedia/Wikidata** (For Concept Relationships)

**What it is:** Free knowledge graph with structured data about concepts, people, and relationships.

**Pros:**
- ✅ Completely free
- ✅ Rich concept relationships
- ✅ Historical timelines
- ✅ Multilingual support

**Cons:**
- ⚠️ Not scholarly-focused
- ⚠️ Variable quality
- ⚠️ Complex SPARQL queries

**How to use:**

```python
import requests

# Get Wikipedia page data
title = "Machine_learning"
url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
response = requests.get(url)
data = response.json()

# Wikidata SPARQL query
sparql_query = """
SELECT ?item ?itemLabel ?inception WHERE {
  ?item wdt:P31 wd:Q11862829.  # instance of academic discipline
  ?item wdt:P571 ?inception.    # inception date
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""
url = "https://query.wikidata.org/sparql"
response = requests.get(url, params={"query": sparql_query, "format": "json"})
results = response.json()["results"]["bindings"]
```

**API Documentation:** 
- Wikipedia: https://www.mediawiki.org/wiki/API:Main_page
- Wikidata: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service

---

## 🛠️ Custom Dataset Creation

### Option A: Manual Curation

Create your own dataset by manually defining ideas and relationships:

```python
# backend/scripts/create_custom_dataset.py
from backend.models import IdeaNode, InfluenceEdge, EvolutionStage
from backend.services import DataStore

store = DataStore("data/evolution_tracker_api")

# Define ideas
ideas = [
    IdeaNode(
        id="CUSTOM001",
        title="Your Idea Title",
        description="Detailed description...",
        stage=EvolutionStage.PHILOSOPHY,
        start_year=1850,
        end_year=1900,
        category="Your Category",
        laureates=["Author 1", "Author 2"],
        motivation="Why this is important",
        keywords=["keyword1", "keyword2"],
        influence_score=0.85
    ),
    # Add more ideas...
]

# Define relationships
edges = [
    InfluenceEdge(
        source_id="CUSTOM001",
        target_id="CUSTOM002",
        influence_type="derived_from",
        influence_weight=0.8,
        evidence="Historical evidence...",
        confidence_score=0.9
    ),
    # Add more edges...
]

# Save to store
for idea in ideas:
    store.add_idea(idea)
for edge in edges:
    store.add_edge(edge)
```

---

### Option B: Import from CSV

Convert existing CSV data:

```python
import csv
from backend.models import IdeaNode, EvolutionStage
from backend.services import DataStore

store = DataStore("data/evolution_tracker_api")

# Read CSV
with open("your_data.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        idea = IdeaNode(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            stage=EvolutionStage.from_string(row["stage"]),
            start_year=int(row["start_year"]),
            end_year=int(row["end_year"]),
            category=row["category"],
            laureates=row["laureates"].split(";"),
            motivation=row["motivation"],
            keywords=row["keywords"].split(";"),
            influence_score=float(row["influence_score"])
        )
        store.add_idea(idea)
```

---

## 📊 Recommended Workflow

### For Testing (Current):
```bash
# Use the test data generator
python backend/scripts/generate_test_data.py
```
- ✅ 26 curated ideas
- ✅ 34 meaningful edges
- ✅ 3 interconnected chains
- ✅ Perfect for development

### For Production (Real Data):
```bash
# Fetch from OpenAlex
python backend/scripts/fetch_openalex.py
```
- ✅ 200 real concepts
- ✅ 500+ edges
- ✅ Real author names
- ✅ Citation-based influence scores

### For Custom Domain:
1. Choose your data source (OpenAlex, Semantic Scholar, etc.)
2. Create a custom fetcher script
3. Map data to IdeaNode and InfluenceEdge models
4. Generate edges based on your domain logic
5. Save to DataStore

---

## 🔧 Enhancing Edge Generation

The current edge generation is basic. Here are advanced strategies:

### 1. **Citation-Based Edges**
```python
# If paper A cites paper B, create edge B → A
if paper_a["references"]:
    for ref in paper_a["references"]:
        if ref["paperId"] in paper_map:
            edge = InfluenceEdge(
                source_id=ref["paperId"],
                target_id=paper_a["paperId"],
                influence_type="validated_by",
                influence_weight=0.7,
                evidence="Citation relationship",
                confidence_score=0.85
            )
```

### 2. **Co-Author Networks**
```python
# Papers with shared authors are related
for paper_a in papers:
    for paper_b in papers:
        shared_authors = set(paper_a["authors"]) & set(paper_b["authors"])
        if shared_authors and paper_a["year"] < paper_b["year"]:
            edge = InfluenceEdge(
                source_id=paper_a["id"],
                target_id=paper_b["id"],
                influence_type="inspired_by",
                influence_weight=len(shared_authors) * 0.2,
                evidence=f"Shared authors: {shared_authors}",
                confidence_score=0.7
            )
```

### 3. **Temporal Chains**
```python
# Connect ideas chronologically within same category
ideas_by_category = {}
for idea in ideas:
    ideas_by_category.setdefault(idea.category, []).append(idea)

for category, cat_ideas in ideas_by_category.items():
    cat_ideas.sort(key=lambda x: x.start_year)
    for i in range(len(cat_ideas) - 1):
        edge = InfluenceEdge(
            source_id=cat_ideas[i].id,
            target_id=cat_ideas[i + 1].id,
            influence_type="derived_from",
            influence_weight=0.6,
            evidence=f"Chronological evolution in {category}",
            confidence_score=0.75
        )
```

### 4. **Keyword Similarity**
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Calculate keyword similarity
texts = [" ".join(idea.keywords) for idea in ideas]
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(texts)
similarity_matrix = cosine_similarity(tfidf_matrix)

# Create edges for similar ideas
for i, idea_a in enumerate(ideas):
    for j, idea_b in enumerate(ideas):
        if i < j and similarity_matrix[i][j] > 0.5:
            edge = InfluenceEdge(
                source_id=idea_a.id,
                target_id=idea_b.id,
                influence_type="inspired_by",
                influence_weight=similarity_matrix[i][j],
                evidence=f"Keyword similarity: {similarity_matrix[i][j]:.2f}",
                confidence_score=0.6
            )
```

---

## 📈 Data Quality Tips

1. **Validate Data:**
   - Check for duplicate IDs
   - Ensure years are within 1800-2126
   - Verify all edges reference existing ideas

2. **Balance the Graph:**
   - Aim for 3-5 edges per idea on average
   - Mix different influence types
   - Create both linear chains and cross-domain connections

3. **Enrich Metadata:**
   - Add meaningful descriptions
   - Include real author names
   - Use accurate keywords
   - Set realistic influence scores

4. **Test Incrementally:**
   - Start with small dataset (20-50 ideas)
   - Verify tree map displays correctly
   - Gradually expand to full dataset

---

## 🚀 Next Steps

1. **Try OpenAlex fetcher:**
   ```bash
   python backend/scripts/fetch_openalex.py
   python -m backend.api
   ```

2. **Explore the data:**
   - Visit http://localhost:5000/api/stats
   - Check http://localhost:5000/api/ideas
   - Test tree map with various ideas

3. **Customize for your domain:**
   - Modify `fetch_openalex.py` to filter specific fields
   - Add custom edge generation logic
   - Enhance with additional data sources

4. **Scale up:**
   - Increase per-page limit (max 200)
   - Fetch multiple pages
   - Combine multiple data sources

---

## 📚 Additional Resources

- **OpenAlex Docs:** https://docs.openalex.org/
- **Semantic Scholar API:** https://api.semanticscholar.org/
- **arXiv API:** https://info.arxiv.org/help/api/
- **CrossRef API:** https://api.crossref.org/
- **PubMed E-utilities:** https://www.ncbi.nlm.nih.gov/books/NBK25501/

---

**Happy Data Hunting! 🎯**
