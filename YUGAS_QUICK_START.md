# Yugas Evolution - Quick Start Guide

## 🚀 Start the Application

```bash
start.bat
```

This opens two windows:
- **Backend**: Flask API on port 5000
- **Frontend**: React app on port 8080

Wait 5-10 seconds for both to start, then open: **http://localhost:8080/yugas**

---

## 🎯 What to Test

### 1. View Rich Content (21 Ideas Available)

Click on any of these ideas to see the enhanced UI:

1. **Saw** - Tool evolution
2. **Drill** - Power tool evolution
3. **Hammer** - Basic tool evolution
4. **Shoes** - Footwear evolution
5. **Velcro** - Fastener evolution
6. **Zipper** - Closure evolution
7. **Telegraph** - Communication evolution
8. **Telephone** - Voice communication
9. **Television** - Visual media
10. **Radio** - Audio broadcast
11. **Camera** - Image capture
12. **Paper** - Writing medium
13. **Pen** - Writing tool
14. **Printing Press** - Mass production
15. **Typewriter** - Text creation
16. **Sewing Machine** - Textile automation
17. **Postal Service** - Mail delivery
18. **Washing Detergent** - Cleaning agent
19. **Dry Cleaning** - Fabric care
20. **Synthetic Fabrics** - Material innovation

**What You'll See**:
- ✅ Time period badges (e.g., "10,000 BCE - 5,000 BCE")
- ✅ Visual statistics cards with icons
- ✅ Numbered characteristics list
- ✅ Long detailed descriptions (200+ words)

### 2. Test Filters

**Time Period Filter** (Interval Tree):
1. Adjust sliders in left panel
2. Example: Set to 5000 BCE - 1000 CE
3. Click "Apply Time Filter"
4. See ideas from that period

**Complexity Filter** (Segment Tree):
1. Adjust complexity sliders
2. Example: Set to 40-80
3. Click "Apply Complexity Filter"
4. See ideas in that range

**Clear Filters**:
- Click "Clear All Filters" button

### 3. Test Evolution Chains

1. Click "Chain" button on any idea card
2. See evolution relationships
3. Example chains:
   - Fire → Cooking → Pressure Cooker
   - Wheel → Bicycle → Motorcycle → Automobile
   - Stone Tools → Hammer → Drill

### 4. Test Search

1. Type in search bar: "cooking" or "transportation"
2. Press Enter
3. See AI-powered semantic search results
4. Notice search type badge (🧠 AI-Powered Search)

### 5. Export Data

1. Click "Export CSV" button (top right)
2. Downloads all 109 ideas with evolutions

---

## 📊 Current Status

- **Total Ideas**: 109
- **With Rich Content**: 21 (fully enhanced)
- **With Basic Content**: 88 (functional but not enhanced)
- **Data Structures**: All working (Interval Tree, Segment Tree, Lineage Graph)

---

## 🔧 To Complete Remaining 88 Ideas

### Option 1: Add API Credits

1. Visit: https://openrouter.ai/settings/credits
2. Add credits to your account
3. Run:
   ```bash
   python -m backend.scripts.regenerate_rich_content_resume
   ```

### Option 2: Leave As Is

The app is fully functional with 21 rich content examples. You can use it as a demo/prototype.

---

## 🛑 Stop the Application

```bash
stop.bat
```

Or press `Ctrl+C` in both terminal windows.

---

## 📚 Full Documentation

See `documentation/` folder for complete guides:
- `CURRENT_STATUS_SUMMARY.md` - What's working now
- `YUGAS_UI_WITH_DATA_STRUCTURES.md` - Complete feature guide
- `UI_ENHANCEMENT_COMPLETE.md` - UI changes summary
- `DATA_STRUCTURES_IN_YUGAS.md` - Data structures explained

---

## 🎨 Visual Guide

### Dashboard
```
┌─────────────────────────────────────────────────┐
│  Interval Tree    Segment Tree    Lineage Graph │
│  🕐 109          ⚡ 109          🔗 24          │
│  O(log n + k)    O(log n)        O(depth)       │
└─────────────────────────────────────────────────┘
```

### Rich Content View
```
┌─────────────────────────────────────────────────┐
│  Satya Yuga (Golden Age)                        │
│  📅 10,000 BCE - 5,000 BCE                      │
├─────────────────────────────────────────────────┤
│  📊 Statistics:                                 │
│  ⚡ Speed: Instantaneous                        │
│  🌟 Energy: Divine/Natural                      │
│  🌍 Accessibility: Universal                    │
├─────────────────────────────────────────────────┤
│  ✨ Characteristics:                            │
│  ① Divine origin                                │
│  ② Flawless cutting ability                     │
│  ③ No need for physical effort                  │
└─────────────────────────────────────────────────┘
```

---

**Ready to explore? Run `start.bat` and open http://localhost:8080/yugas** 🚀
