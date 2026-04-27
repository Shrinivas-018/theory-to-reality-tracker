# Tree Map Visualization - Test Guide

## ✅ Test Data Generated Successfully

**26 ideas** across 3 evolution chains with **34 edges** (23 linear + 11 cross-domain)

---

## 🎯 Best Ideas to Test

### 1. **CS005 - Operating Systems** (Middle of CS chain)
- **Has**: 4 ancestors, 5 descendants
- **Shows**: Balanced tree with both directions
- **Category**: Computer Science
- **Year**: 1969-1985

### 2. **PHY004 - Quantum Mechanics** (Middle of Physics chain)
- **Has**: 3 ancestors, 4 descendants  
- **Shows**: Balanced tree with cross-domain connections
- **Category**: Physics
- **Year**: 1900-1930

### 3. **BIO004 - DNA Structure** (Middle of Biology chain)
- **Has**: 3 ancestors, 4 descendants
- **Shows**: Balanced tree structure
- **Category**: Biology
- **Year**: 1953-1970

### 4. **CS008 - Machine Learning** (Cross-domain hub)
- **Has**: 7 ancestors, 2 descendants
- **Shows**: Rich tree with connections from Biology and Physics
- **Category**: Computer Science
- **Year**: 1980-2010
- **Special**: Connected to Evolution (BIO002) and Genome Project (BIO006)

### 5. **PHY006 - Semiconductor Physics** (Cross-domain connector)
- **Has**: 5 ancestors, 2 descendants
- **Shows**: Physics → Computer Science connection
- **Category**: Physics
- **Year**: 1947-1970
- **Special**: Connects to Stored-Program Computer (CS003)

### 6. **BIO006 - Human Genome Project** (Cross-domain connector)
- **Has**: 5 ancestors, 2 descendants
- **Shows**: Biology → Computer Science connection
- **Category**: Biology
- **Year**: 1990-2003
- **Special**: Connects to Machine Learning (CS008)

---

## 📊 Evolution Chains

### Computer Science Chain (10 ideas)
```
CS001 Mathematical Logic (1850)
  ↓
CS002 Turing Machine (1936)
  ↓
CS003 Stored-Program Computer (1945)
  ↓
CS004 High-Level Programming Languages (1957)
  ↓
CS005 Operating Systems (1969) ← TEST THIS
  ↓
CS006 Relational Databases (1970)
  ↓
CS007 Internet Protocol Suite (1974)
  ↓
CS008 Machine Learning (1980) ← TEST THIS (cross-domain)
  ↓
CS009 Cloud Computing (2006)
  ↓
CS010 Large Language Models (2017)
```

### Physics Chain (8 ideas)
```
PHY001 Classical Mechanics (1800)
  ↓
PHY002 Thermodynamics (1824)
  ↓
PHY003 Electromagnetism (1861)
  ↓
PHY004 Quantum Mechanics (1900) ← TEST THIS
  ↓
PHY005 Nuclear Physics (1932)
  ↓
PHY006 Semiconductor Physics (1947) ← TEST THIS (cross-domain)
  ↓
PHY007 Laser Technology (1960)
  ↓
PHY008 Quantum Computing (1994)
```

### Biology Chain (8 ideas)
```
BIO001 Cell Theory (1838)
  ↓
BIO002 Evolution by Natural Selection (1859)
  ↓
BIO003 Mendelian Genetics (1866)
  ↓
BIO004 DNA Structure (1953) ← TEST THIS
  ↓
BIO005 Genetic Engineering (1973)
  ↓
BIO006 Human Genome Project (1990) ← TEST THIS (cross-domain)
  ↓
BIO007 CRISPR Gene Editing (2012)
  ↓
BIO008 Synthetic Biology (2010)
```

---

## 🔗 Cross-Domain Connections (11 edges)

### Physics → Computer Science
- PHY006 (Semiconductors) → CS003 (Stored-Program Computer)
- PHY004 (Quantum Mechanics) → CS008 (Machine Learning)
- PHY008 (Quantum Computing) → CS010 (LLMs)

### Biology → Computer Science
- BIO002 (Evolution) → CS008 (Machine Learning)
- BIO004 (DNA) → CS006 (Databases)
- BIO006 (Genome Project) → CS008 (Machine Learning)

### Computer Science → Biology
- CS008 (Machine Learning) → BIO007 (CRISPR)
- CS004 (Programming) → BIO005 (Genetic Engineering)
- CS009 (Cloud) → BIO008 (Synthetic Biology)

### Physics → Biology
- PHY003 (Electromagnetism) → BIO001 (Cell Theory)
- PHY007 (Lasers) → BIO006 (Genome Project)

---

## 🚀 How to Test

### Step 1: Restart Backend Server
```bash
# Close the existing backend terminal window
# Then run:
python -m backend.api
```

### Step 2: Verify Data Loaded
Visit: http://localhost:5000/api/stats

Should show:
```json
{
  "total_ideas": 26,
  "total_edges": 34
}
```

### Step 3: Refresh Frontend
- Open: http://localhost:8080
- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### Step 4: Test Tree Map
1. Click on **"Operating Systems"** (CS005)
2. Look at the right sidebar → "Evolutionary Lineage" section
3. You should see:
   - **4 ancestor nodes** above (pink connections)
   - **1 root node** in center (Operating Systems)
   - **5 descendant nodes** below (violet connections)
   - Interactive hover effects
   - Smooth animations

### Step 5: Test Cross-Domain
1. Click on **"Machine Learning"** (CS008)
2. You should see connections from:
   - Computer Science chain (CS001-CS007)
   - Biology (Evolution, Genome Project)
   - Physics (Quantum Mechanics)

---

## 🎨 What You Should See

### Tree Map Features:
✅ **Hierarchical Layout**: Ancestors above, root center, descendants below  
✅ **Color-Coded Edges**: Pink (ancestors), Violet (descendants)  
✅ **Interactive Nodes**: Hover to highlight, click to navigate  
✅ **Smooth Animations**: Staggered entrance with Framer Motion  
✅ **Stage Colors**: Purple (philosophy), Blue (validation), Orange (engineering), Green (modern)  
✅ **Responsive**: Adapts to sidebar width  
✅ **Empty State**: Shows message for standalone ideas  

### Empty State:
If you click on an idea with no connections, you'll see:
> "This is an emergent standalone concept with no explicitly mapped ancestors or descendants in the knowledge graph."

---

## 🐛 Troubleshooting

### Tree Map Not Showing?
1. **Check backend stats**: Visit http://localhost:5000/api/stats
   - Should show `total_edges: 34`
   - If 0, restart backend server

2. **Check browser console**: Press F12
   - Look for API errors
   - Check network tab for failed requests

3. **Test API directly**:
   ```bash
   curl http://localhost:5000/api/ideas/CS005/ancestors
   curl http://localhost:5000/api/ideas/CS005/descendants
   ```
   - Should return arrays of ideas

4. **Hard refresh**: Ctrl+Shift+R
   - Clears cached frontend code

### Still Not Working?
- Verify both servers are running (backend on 5000, frontend on 8080)
- Check for CORS errors in browser console
- Ensure `data/evolution_tracker_api/` has both `ideas.json` and `edges.json`
- Try a different browser

---

## 📝 Notes

- **Data is persistent**: Saved in `data/evolution_tracker_api/`
- **Regenerate anytime**: Run `python backend/scripts/generate_test_data.py`
- **Original data**: Backed up if you want to restore it
- **Cross-domain edges**: Show how different fields influence each other
- **Realistic timeline**: Ideas span from 1800 to 2024

---

## 🎉 Success Criteria

You'll know it's working when:
1. ✅ Clicking "Operating Systems" shows a tree with 10 total nodes
2. ✅ Nodes are arranged vertically (ancestors up, descendants down)
3. ✅ Edges are curved SVG paths (pink and violet)
4. ✅ Hovering a node highlights its connections
5. ✅ Clicking a node navigates to that idea's detail panel
6. ✅ Animations are smooth and staggered
7. ✅ "Machine Learning" shows cross-domain connections

**Happy Testing! 🚀**
