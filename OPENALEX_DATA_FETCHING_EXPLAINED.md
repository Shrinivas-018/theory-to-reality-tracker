# OpenAlex Data Fetching - Complete Explanation

## Overview
This document explains how data is fetched from OpenAlex API and transformed into the Evolution Tracker dataset.

## What is OpenAlex?

**OpenAlex** is a free, open catalog of scholarly works, authors, institutions, and concepts. It contains:
- 250+ million scholarly works
- 200+ million authors
- 65,000+ concepts (topics/fields)
- Citation relationships
- Metadata about research

**Website**: https://openalex.org/
**API Docs**: https://docs.openalex.org/

## Fetching Strategy

### Two Approaches Available:

#### 1. Basic Fetcher (`fetch_openalex.py`)
- Simple, straightforward approach
- Uses only OpenAlex API data
- Rule-based edge generation
- Faster but less intelligent

#### 2. LLM-Enhanced Fetcher (`fetch_openalex_with_llm.py`) ⭐ RECOMMENDED
- Uses Google Gemini AI for intelligent analysis
- Creates meaningful evolution chains
- Better relationship detection
- Higher quality dataset

## Data Fetching Process (Step-by-Step)

### Step 1: Fetch Concepts from OpenAlex

**API Endpoint**:
```
https://api.openalex.org/concepts?per-page=200&sort=works_count:desc
```

**What it fetches**:
- Top 200 concepts sorted by scholarly impact
- Each concept has:
  - `id`: Unique identifier (e.g., "C41008148")
  - `display_name`: Human-readable name (e.g., "Computer Science")
  - `description`: Brief explanation
  - `level`: Hierarchy level (0-4)
  - `works_count`: Number of scholarly works
  - `ancestors`: Parent concepts
  - `related_concepts`: Similar concepts

**Sorting Criteria**:
- **Primary**: `works_count` (descending)
- **Why**: More works = more influential/important
- **Result**: Gets the most impactful concepts first

**Example Response**:
```json
{
  "id": "https://openalex.org/C41008148",
  "display_name": "Computer science",
  "description": "Study of computation and information processing",
  "level": 0,
  "works_count": 172164242,
  "ancestors": [],
  "related_concepts": [
    {"id": "C154945302", "display_name": "Artificial intelligence"},
    {"id": "C119857082", "display_name": "Machine learning"}
  ]
}
```

### Step 2: Concept Scoring & Optimization

**Scoring Factors** (LLM-enhanced version):

1. **Works Count** (40 points max)
   - Formula: `min(works_count / 1,000,000, 1.0) * 40`
   - Why: More works = more influential
   - Example: 172M works = 40 points

2. **Level Diversity** (30 points max)
   - Level 0 (foundational): 30 points
   - Level 1 (major field): 25 points
   - Level 2 (subfield): 20 points
   - Level 3+ (specific): 15 points
   - Why: Want mix of broad and specific concepts

3. **Ancestor Count** (20 points max)
   - Formula: `min(ancestor_count * 5, 20)`
   - Why: Better for tree visualization
   - Example: 4 ancestors = 20 points

4. **Related Concepts** (10 points max)
   - Formula: `min(related_count * 2, 10)`
   - Why: Better connectivity
   - Example: 5 related = 10 points

**Total Score**: Up to 100 points per concept

**Selection**: Top 200 concepts by score

### Step 3: Map to Evolution Stages

**OpenAlex Level → Evolution Stage Mapping**:

| OpenAlex Level | Evolution Stage | Years | Reasoning |
|---------------|----------------|-------|-----------|
| 0 | Philosophy | 1800-1850 | Foundational concepts, theoretical |
| 1 | Scientific Validation | 1850-1950 | Major fields, experimental proof |
| 2 | Engineering Application | 1950-2000 | Practical applications, technology |
| 3+ | Modern Technology | 2000-2025 | Current implementations, active use |

**Why this mapping?**
- Level 0 concepts are broad, foundational (like "Physics")
- Level 1 concepts are established fields (like "Quantum Mechanics")
- Level 2 concepts are applications (like "Quantum Computing")
- Level 3+ concepts are specific technologies (like "Quantum Cryptography")

### Step 4: Calculate Influence Scores

**Formula**:
```python
influence_score = works_count / max_works_count
```

**Normalization**:
- Range: 0.1 to 1.0
- Minimum: 0.1 (ensures all ideas have some influence)
- Maximum: 1.0 (most influential concept)

**Example**:
- Computer Science: 172M works → 1.0 (100%)
- Physics: 86M works → 0.50 (50%)
- Quantum Computing: 1M works → 0.01 → 0.1 (10% minimum)

### Step 5: Fetch Author Names

**Two Methods**:

#### Method 1: Curated Database (Preferred)
```python
KNOWN_AUTHORS = {
    "Computer science": ["Alan Turing", "John von Neumann", "Claude Shannon"],
    "Physics": ["Isaac Newton", "Albert Einstein", "Richard Feynman"],
    "Biology": ["Charles Darwin", "Gregor Mendel", "Francis Crick"],
    # ... 20+ more
}
```

**Why curated?**
- Historically accurate
- Well-known contributors
- Consistent quality

#### Method 2: OpenAlex Works API (Fallback)
```
https://api.openalex.org/works?filter=concepts.id:{concept_id}&sort=cited_by_count:desc&per-page=5
```

**Process**:
1. Fetch top 5 most-cited works for the concept
2. Extract author names from each work
3. Take first 3 unique authors
4. Fallback to "Notable Researchers" if none found

### Step 6: Generate Relationships (Edges)

#### A. OpenAlex Ancestor Relationships

**Source**: `ancestors` field in concept data

**Logic**:
```python
for ancestor in concept.ancestors:
    create_edge(
        source=ancestor.id,
        target=concept.id,
        type="derived_from",
        weight=0.75,
        confidence=0.85
    )
```

**Example**:
- "Quantum Computing" has ancestor "Quantum Mechanics"
- Creates edge: Quantum Mechanics → Quantum Computing

#### B. Temporal Evolution Chains

**Logic**:
1. Group concepts by category
2. Sort by start_year (proxy for evolution)
3. Connect sequential concepts

```python
# Within "Computer Science" category:
# 1800-1850: Computer Science (Philosophy)
# 1850-1950: Algorithms (Scientific Validation)
# 1950-2000: Programming Languages (Engineering)
# 2000-2025: Machine Learning (Modern Technology)

# Creates edges:
# Computer Science → Algorithms
# Algorithms → Programming Languages
# Programming Languages → Machine Learning
```

**Why?**
- Shows chronological evolution
- Represents how fields developed over time
- Creates meaningful progression

#### C. Related Concepts (Limited)

**Source**: `related_concepts` field

**Logic**:
```python
for related in concept.related_concepts[:2]:  # Limit to 2
    if related.influence_score > concept.influence_score:
        create_edge(
            source=concept.id,
            target=related.id,
            type="inspired_by",
            weight=0.5,
            confidence=0.6
        )
```

**Why limited?**
- Prevents too many edges (performance)
- Only connects to more influential concepts
- Avoids bidirectional edges

#### D. LLM-Generated Evolution Chains (Enhanced Version Only)

**Process**:
1. Group concepts by category
2. Send to Google Gemini with prompt:

```
Analyze these Computer Science concepts and identify evolutionary relationships.
Create a chronological evolution chain showing how ideas evolved from foundational to modern.

Concepts:
- Computer science (ID: C41008148, Level: 0): Study of computation...
- Algorithms (ID: C154945302, Level: 1): Step-by-step procedures...
- Machine learning (ID: C119857082, Level: 2): Algorithms that learn...

Return a JSON array of evolution chains. Each chain is an array of concept IDs.
Example: [["C41008148", "C154945302", "C119857082"]]

Focus on:
1. Chronological progression (earlier → later)
2. Conceptual dependencies (foundation → application)
3. Historical influence (what enabled what)
```

3. Parse LLM response
4. Create edges along each chain

**Advantages**:
- Intelligent relationship detection
- Considers semantic meaning
- Better than rule-based approach
- Creates meaningful evolution paths

### Step 7: Save to DataStore

**File Structure**:
```
data/evolution_tracker_api/
├── ideas.json (All IdeaNode objects)
└── edges.json (All InfluenceEdge objects)
```

**Backup**:
- Existing data backed up to `data/evolution_tracker_api_backup_{timestamp}/`
- Prevents data loss
- Allows rollback if needed

## Data Quality Metrics

### Dataset Statistics (Typical):
- **Total Ideas**: 200-220
- **Total Edges**: 250-300
- **Avg Edges per Idea**: 1.2-1.5
- **Categories**: 20-30 unique
- **Evolution Stages**: 4 (balanced distribution)

### Quality Indicators:
- ✅ High influence scores for foundational concepts
- ✅ Chronological progression in edges
- ✅ Balanced stage distribution
- ✅ Meaningful category groupings
- ✅ Real author names (not "Unknown")

## Comparison: Basic vs LLM-Enhanced

| Feature | Basic Fetcher | LLM-Enhanced Fetcher |
|---------|--------------|---------------------|
| **Speed** | Fast (~30 seconds) | Slower (~2-3 minutes) |
| **Quality** | Good | Excellent |
| **Edge Intelligence** | Rule-based | AI-analyzed |
| **Evolution Chains** | Simple temporal | Semantic + temporal |
| **Requires API Key** | No | Yes (Gemini) |
| **Recommended For** | Quick testing | Production use |

## How to Run

### Basic Fetcher:
```bash
cd idea_tracker
python backend/scripts/fetch_openalex.py
```

### LLM-Enhanced Fetcher (Recommended):
```bash
# 1. Set up Gemini API key
echo "GEMINI_API_KEY=your_key_here" >> .env

# 2. Run fetcher
python backend/scripts/fetch_openalex_with_llm.py
```

### Get Gemini API Key:
1. Visit: https://aistudio.google.com/
2. Click "Get API Key"
3. Create new key (free tier available)
4. Copy key to `.env` file

## Customization Options

### Change Number of Concepts:
```python
# In fetch_openalex_with_llm.py, line ~450
MAX_CONCEPTS = 200  # Change to 100, 300, etc.
```

### Change Scoring Weights:
```python
# In optimize_dataset() function
score += min(works_count / 1000000, 1.0) * 40  # Works count weight
level_bonus = {0: 30, 1: 25, 2: 20, 3: 15}     # Level weights
score += min(ancestors_count * 5, 20)          # Ancestor weight
score += min(related_count * 2, 10)            # Related weight
```

### Change Evolution Stage Mapping:
```python
# In map_level_to_stage_and_year()
if level == 0:
    return EvolutionStage.PHILOSOPHY, 1700, 1800  # Earlier years
elif level == 1:
    return EvolutionStage.SCIENTIFIC_VALIDATION, 1800, 1900
# ...
```

### Add More Curated Authors:
```python
# In KNOWN_AUTHORS dictionary
KNOWN_AUTHORS = {
    "Your Field": ["Author 1", "Author 2", "Author 3"],
    # ...
}
```

## API Rate Limits

### OpenAlex:
- **Limit**: 10 requests per second (polite)
- **Recommended**: 5 requests per second
- **Implementation**: 0.2 second delay between requests
- **No API key required**: Free and open

### Google Gemini:
- **Free Tier**: 60 requests per minute
- **Implementation**: 1 second delay between requests
- **Requires API key**: Free tier available

## Troubleshooting

### Issue: "Failed to fetch concepts"
**Solution**: Check internet connection, OpenAlex might be down

### Issue: "GEMINI_API_KEY not found"
**Solution**: Add key to `.env` file or use basic fetcher

### Issue: "Too few edges generated"
**Solution**: Increase MAX_CONCEPTS or use LLM-enhanced version

### Issue: "Concepts not in English"
**Solution**: OpenAlex is multilingual, filter by language if needed

### Issue: "Missing author names"
**Solution**: Add to KNOWN_AUTHORS dictionary

## Best Practices

1. **Use LLM-Enhanced Version**: Better quality, worth the extra time
2. **Set Gemini API Key**: Enables intelligent edge generation
3. **Backup Data**: Automatic, but verify backups exist
4. **Start Small**: Test with 50-100 concepts first
5. **Review Results**: Check data quality before using in production
6. **Update Regularly**: OpenAlex data changes, refetch periodically

## Data Flow Diagram

```
OpenAlex API
    ↓
Fetch Concepts (sorted by works_count)
    ↓
Score & Optimize (select top 200)
    ↓
Map to Evolution Stages (level → stage)
    ↓
Calculate Influence Scores (normalize)
    ↓
Fetch/Assign Authors (curated + API)
    ↓
Generate Edges:
    ├─ Ancestor relationships (OpenAlex)
    ├─ Temporal chains (chronological)
    ├─ Related concepts (limited)
    └─ LLM evolution chains (if available)
    ↓
Save to DataStore (JSON files)
    ↓
Load in Backend API
    ↓
Display in Frontend
```

## Summary

**Data is fetched based on**:
1. ✅ **Scholarly Impact**: Works count (most influential concepts)
2. ✅ **Hierarchy Level**: Mix of foundational and specific concepts
3. ✅ **Connectivity**: Concepts with ancestors and related concepts
4. ✅ **Quality Score**: Multi-factor scoring (works, level, ancestors, related)
5. ✅ **Evolution Logic**: Chronological and semantic relationships
6. ✅ **AI Analysis**: LLM-identified evolution chains (enhanced version)

**Result**: High-quality, interconnected dataset showing the evolution of scientific ideas from theory to reality!
