# Influence Score Calculation Guide

## Overview

The **influence_score** is a normalized metric (0.0 to 1.0) that represents the relative importance, impact, or significance of an idea within the evolution tracker system.

---

## 📊 Calculation Methods

The influence score is calculated differently depending on the data source:

### **1. OpenAlex Data (Real Scholarly Data)**

**Location:** `backend/scripts/fetch_openalex.py` (lines 100-130)

**Formula:**
```python
max_score = max(c.get('works_count', 1) for c in concepts)
score = c.get('works_count', 0) / max_score
influence_score = round(max(0.1, score), 4)
```

**Explanation:**
- **works_count**: Number of scholarly works (papers, articles) associated with this concept in OpenAlex database
- **Normalization**: Divided by the maximum works_count across all fetched concepts
- **Minimum floor**: Ensures no score goes below 0.1 (10%)
- **Range**: 0.1 to 1.0
- **Precision**: Rounded to 4 decimal places

**Example:**
```
Concept A: 50,000 works
Concept B: 25,000 works  
Concept C: 10,000 works
Max = 50,000

Influence Scores:
- Concept A: 50,000 / 50,000 = 1.0000
- Concept B: 25,000 / 50,000 = 0.5000
- Concept C: 10,000 / 50,000 = 0.2000
```

**What it represents:**
- **High score (0.8-1.0)**: Widely studied, highly cited, foundational concepts
- **Medium score (0.4-0.7)**: Important but more specialized concepts
- **Low score (0.1-0.3)**: Emerging or niche concepts

---

### **2. Test Data (Manual Curation)**

**Location:** `backend/scripts/generate_test_data.py`

**Method:** Manually assigned based on historical significance

**Examples:**
```python
{
    "title": "Large Language Models",
    "influence_score": 1.0,  # Maximum - revolutionary impact
}

{
    "title": "Internet Protocol Suite",
    "influence_score": 0.98,  # Near maximum - foundational technology
}

{
    "title": "Turing Machine",
    "influence_score": 0.95,  # Very high - theoretical foundation
}

{
    "title": "Relational Databases",
    "influence_score": 0.87,  # High - widespread adoption
}

{
    "title": "Mathematical Logic",
    "influence_score": 0.85,  # High - foundational but older
}
```

**Criteria for manual assignment:**
1. **Historical Impact**: How much did it change the field?
2. **Adoption**: How widely is it used today?
3. **Citations**: How often is it referenced?
4. **Foundational Nature**: Is it a prerequisite for other ideas?
5. **Current Relevance**: Is it still actively used/studied?

---

## 🎯 Usage in the System

### **1. Visual Representation**

**Frontend Display:**
- Progress bar at bottom of each idea card
- Width proportional to influence_score
- Color matches the evolution stage

```typescript
// In EvolutionTracker.tsx
<rect
  x={15}
  y={pos.h - 8}
  width={(pos.w - 30) * pos.idea.influence_score}  // Width based on score
  height={3}
  rx={1.5}
  fill={pos.color}
  opacity={0.8}
/>
```

### **2. AI Predictions**

**Dormancy Detection:**
Used as a factor in determining if an idea is "dormant" (has potential but underutilized)

**Evolution Forecasting:**
```python
# In ai_prediction.py (line 347)
prob_tech = min(0.3 + idea.influence_score * 0.3 + connectivity * 5, 0.95)
```
- Higher influence_score increases probability of reaching technology stage
- Weighted at 30% in the heuristic forecast

### **3. Statistics Dashboard**

**Average Influence:**
```python
# Displayed in stats cards
avg_influence = sum(idea.influence_score for idea in ideas) / len(ideas)
```

Shows overall "importance" of the dataset

---

## 📈 Score Distribution

### **Typical Distribution (OpenAlex Data):**

```
1.0         ████ (1-2%)    - Foundational concepts
0.8-0.9     ████████ (5-8%) - Major breakthroughs
0.6-0.7     ████████████ (10-15%) - Important concepts
0.4-0.5     ████████████████ (20-25%) - Established ideas
0.2-0.3     ████████████████████ (30-35%) - Specialized topics
0.1-0.2     ████████████ (15-20%) - Emerging/niche areas
```

### **Test Data Distribution:**

```
1.0         █ (1 idea)     - LLMs
0.95-0.99   ████ (4 ideas) - Quantum Mechanics, Turing Machine, etc.
0.85-0.94   ████████ (8 ideas) - Operating Systems, Databases, etc.
0.80-0.84   ████ (4 ideas) - Cell Theory, Evolution, etc.
< 0.80      █████████ (9 ideas) - Supporting concepts
```

---

## 🔧 Validation Rules

**Location:** `backend/models/validation.py` (lines 65-71)

```python
# Requirement 15.5: influence_score must be between 0.0 and 1.0
if not (0.0 <= idea.influence_score <= 1.0):
    raise ValueError(
        f"IdeaNode influence_score must be between 0.0 and 1.0, "
        f"got {idea.influence_score}"
    )
```

**Constraints:**
- ✅ Minimum: 0.0 (though OpenAlex enforces 0.1 floor)
- ✅ Maximum: 1.0
- ✅ Type: Float
- ✅ Precision: Typically 4 decimal places

---

## 🎨 Visual Indicators

### **Color Coding (by Stage):**
- **Purple** (Philosophy): 0.1-1.0
- **Blue** (Scientific Validation): 0.1-1.0
- **Orange** (Engineering Application): 0.1-1.0
- **Green** (Modern Technology): 0.1-1.0

### **Bar Length:**
- **Full bar (100%)**: influence_score = 1.0
- **Half bar (50%)**: influence_score = 0.5
- **Quarter bar (25%)**: influence_score = 0.25
- **Thin bar (10%)**: influence_score = 0.1

---

## 📝 How to Set Custom Scores

### **When Creating New Ideas:**

```python
from backend.models import IdeaNode, EvolutionStage

idea = IdeaNode(
    id="my_idea_001",
    title="My Revolutionary Idea",
    description="...",
    stage=EvolutionStage.MODERN_TECHNOLOGY,
    start_year=2020,
    category="Technology",
    laureates=["Jane Doe"],
    motivation="Game-changing innovation",
    keywords=["innovation", "breakthrough"],
    influence_score=0.92  # Set based on significance
)
```

### **Guidelines for Manual Assignment:**

| Score Range | Criteria | Examples |
|-------------|----------|----------|
| **0.95-1.0** | Revolutionary, foundational, universally adopted | Internet, DNA Structure, Quantum Mechanics |
| **0.85-0.94** | Major breakthrough, widespread impact | Operating Systems, Machine Learning, CRISPR |
| **0.70-0.84** | Significant contribution, well-established | Databases, Compilers, Lasers |
| **0.50-0.69** | Important but specialized | Specific algorithms, techniques |
| **0.30-0.49** | Emerging or niche | New research areas, experimental tech |
| **0.10-0.29** | Early stage or very specialized | Preliminary concepts, narrow applications |

---

## 🔄 Future Enhancements

### **Potential Improvements:**

1. **Dynamic Calculation:**
   - Recalculate based on number of descendant ideas
   - Factor in edge weights (influence_weight)
   - Use PageRank centrality from lineage graph

2. **Time Decay:**
   - Reduce score for very old ideas
   - Boost score for recent breakthroughs

3. **Citation Integration:**
   - Pull real-time citation counts from APIs
   - Update scores periodically

4. **User Voting:**
   - Allow community to vote on importance
   - Combine with algorithmic score

5. **Multi-Factor Scoring:**
   ```python
   influence_score = (
       0.4 * citation_score +
       0.3 * adoption_score +
       0.2 * centrality_score +
       0.1 * recency_score
   )
   ```

---

## 📚 Related Files

- **Model Definition**: `backend/models/idea_node.py`
- **Validation**: `backend/models/validation.py`
- **OpenAlex Fetcher**: `backend/scripts/fetch_openalex.py`
- **Test Data Generator**: `backend/scripts/generate_test_data.py`
- **AI Predictions**: `backend/services/ai_prediction.py`
- **Frontend Display**: `frontend/src/pages/EvolutionTracker.tsx`

---

## 🎯 Summary

The **influence_score** is a simple but powerful metric that:
- ✅ Normalizes importance across different ideas
- ✅ Provides visual feedback in the UI
- ✅ Influences AI predictions
- ✅ Helps identify high-impact concepts
- ✅ Enables comparative analysis

It's calculated either from **real scholarly data** (works_count) or **manually curated** based on historical significance, always normalized to the 0.0-1.0 range.
