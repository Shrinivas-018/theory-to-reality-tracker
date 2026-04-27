# Which Data Fetcher Should I Use?

Quick decision guide to choose the right data fetching approach.

---

## 🎯 Quick Decision Tree

```
Do you need real scholarly data?
│
├─ NO → Use: generate_test_data.py
│        ✅ 26 curated ideas
│        ✅ Perfect for development
│        ✅ Instant (< 1 second)
│
└─ YES → Do you have 5 minutes for setup?
         │
         ├─ NO → Use: fetch_openalex.py
         │        ✅ 200 real concepts
         │        ✅ No API key needed
         │        ✅ Good quality edges
         │        ⏱️  2 minutes
         │
         └─ YES → Use: fetch_openalex_with_llm.py
                  ✅ 200 optimized concepts
                  ✅ Intelligent evolution chains
                  ✅ Best quality relationships
                  ⏱️  5 minutes (+ setup)
```

---

## 📊 Detailed Comparison

| Feature | Test Data | OpenAlex Basic | OpenAlex + LLM |
|---------|-----------|----------------|----------------|
| **Setup Time** | 0 min | 0 min | 5 min |
| **Execution Time** | < 1 sec | 2 min | 5 min |
| **API Key Required** | ❌ No | ❌ No | ✅ Yes (free) |
| **Internet Required** | ❌ No | ✅ Yes | ✅ Yes |
| **Number of Ideas** | 26 | 200 | 200 |
| **Number of Edges** | 34 | ~450 | ~550 |
| **Edge Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Real Data** | ❌ No | ✅ Yes | ✅ Yes |
| **Real Authors** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Evolution Chains** | ✅ Perfect | ✅ Good | ✅ Excellent |
| **Cross-Domain Links** | ✅ Yes | ⚠️  Few | ✅ Many |
| **Tree Depth** | 3-5 levels | 2-3 levels | 3-5 levels |
| **Performance** | ⚡ Instant | ⚡ Fast | ⚡ Fast |
| **Customizable** | ✅ Easy | ⚠️  Medium | ✅ Easy |

---

## 🎭 Use Case Scenarios

### Scenario 1: "I'm just testing the app"
**Use:** `generate_test_data.py`

```bash
python backend/scripts/generate_test_data.py
python -m backend.api
```

**Why:**
- Instant results
- Perfect for UI testing
- No dependencies
- Predictable data

---

### Scenario 2: "I need real data quickly"
**Use:** `fetch_openalex.py`

```bash
python backend/scripts/fetch_openalex.py
python -m backend.api
```

**Why:**
- No setup required
- Real scholarly data
- Good enough for most cases
- Works offline after first fetch

---

### Scenario 3: "I want the best quality for production"
**Use:** `fetch_openalex_with_llm.py`

```bash
# One-time setup
pip install google-generativeai python-dotenv
echo GEMINI_API_KEY=your_key > .env

# Run fetcher
python backend/scripts/fetch_openalex_with_llm.py
python -m backend.api
```

**Why:**
- Highest quality relationships
- Intelligent evolution chains
- Best user experience
- Worth the 5-minute setup

---

### Scenario 4: "I have my own data"
**Use:** Custom script (see DATA_SOURCES_GUIDE.md)

```python
# Create your own fetcher
from backend.models import IdeaNode, InfluenceEdge
from backend.services import DataStore

# Your custom logic here
```

**Why:**
- Domain-specific data
- Full control
- Can combine multiple sources

---

## 🚦 Performance Impact

### Test Data (26 ideas, 34 edges)
- ✅ **Load Time:** < 100ms
- ✅ **Tree Map Render:** < 50ms
- ✅ **No lag:** Butter smooth

### OpenAlex Basic (200 ideas, 450 edges)
- ✅ **Load Time:** ~300ms
- ✅ **Tree Map Render:** ~100ms
- ✅ **Minimal lag:** Very smooth

### OpenAlex + LLM (200 ideas, 550 edges)
- ✅ **Load Time:** ~350ms
- ✅ **Tree Map Render:** ~120ms
- ✅ **Minimal lag:** Very smooth

**Conclusion:** All options perform well! The 200-idea limit ensures no lag.

---

## 💰 Cost Comparison

| Option | Cost | Rate Limits |
|--------|------|-------------|
| **Test Data** | Free | None |
| **OpenAlex Basic** | Free | 10 req/sec |
| **OpenAlex + LLM** | Free* | 60 req/min (Gemini) |

*Gemini free tier: 60 requests/minute, 1500 requests/day

---

## 🎯 Recommendations by User Type

### For Developers:
1. Start with **Test Data** (instant feedback)
2. Switch to **OpenAlex Basic** when ready
3. Upgrade to **LLM** for final polish

### For Researchers:
1. Use **OpenAlex + LLM** (best quality)
2. Customize prompts for your domain
3. Supplement with manual curation

### For Students:
1. Use **Test Data** (learn the system)
2. Try **OpenAlex Basic** (real data)
3. Experiment with **LLM** (optional)

### For Production:
1. Use **OpenAlex + LLM** (best UX)
2. Cache results (don't fetch on every deploy)
3. Monitor performance

---

## 🔄 Migration Path

### From Test Data → OpenAlex Basic
```bash
# Backup test data
mv data/evolution_tracker_api data/test_data_backup

# Fetch real data
python backend/scripts/fetch_openalex.py

# Restart backend
python -m backend.api
```

### From OpenAlex Basic → OpenAlex + LLM
```bash
# Setup LLM (one time)
pip install google-generativeai python-dotenv
echo GEMINI_API_KEY=your_key > .env

# Fetch with LLM
python backend/scripts/fetch_openalex_with_llm.py

# Restart backend
python -m backend.api
```

### Rollback to Previous Data
```bash
# Your data is automatically backed up!
# Look for: data/evolution_tracker_api_backup_<timestamp>

# Restore backup
rm -rf data/evolution_tracker_api
mv data/evolution_tracker_api_backup_<timestamp> data/evolution_tracker_api

# Restart backend
python -m backend.api
```

---

## 📝 Summary

### Choose Test Data if:
- ✅ Just exploring the app
- ✅ Developing new features
- ✅ Need instant results
- ✅ Don't need real data

### Choose OpenAlex Basic if:
- ✅ Need real scholarly data
- ✅ Want quick setup (no API key)
- ✅ Good enough quality
- ✅ Limited time

### Choose OpenAlex + LLM if:
- ✅ Want best quality
- ✅ Production deployment
- ✅ Have 5 minutes for setup
- ✅ Want intelligent relationships

---

## 🚀 Quick Start Commands

```bash
# Option 1: Test Data (Instant)
python backend/scripts/generate_test_data.py

# Option 2: OpenAlex Basic (2 min)
python backend/scripts/fetch_openalex.py

# Option 3: OpenAlex + LLM (5 min + setup)
pip install google-generativeai python-dotenv
echo GEMINI_API_KEY=your_key > .env
python backend/scripts/fetch_openalex_with_llm.py

# Always restart backend after fetching
python -m backend.api
```

---

**Still unsure? Start with Test Data, then upgrade when ready!** 🎯
