# Frontend — Theory-to-Reality Evolution Tracker

Interactive React dashboard for visualizing idea evolution with force-directed graphs, animated timelines, and AI prediction displays.

---

## Structure

```
frontend/src/
├── App.tsx                          # Root app with routing
├── main.tsx                         # Entry point
├── pages/
│   ├── EvolutionTracker.tsx         # Main dashboard (all 4 tabs)
│   └── NotFound.tsx                 # 404 page
├── components/ui/                   # Radix-based UI component library
├── hooks/
│   ├── use-mobile.tsx               # Responsive breakpoint hook
│   └── use-toast.ts                 # Toast notification hook
└── lib/
    └── utils.ts                     # Utility functions (cn helper)
```

---

## Features

### Timeline Tab
- Animated vertical timeline of ideas sorted chronologically
- Search by title, description, or keywords
- Filter by evolution stage (Philosophy, Scientific Validation, Engineering, Modern Technology)
- Filter by category chain and year range
- Influence score progress bars per idea

### Lineage Graph Tab
- Interactive force-directed graph powered by `react-force-graph-2d`
- Nodes colored by evolution stage, sized by influence score
- Cross-chain edges shown as dashed purple lines
- Zoom, pan, and hover for details
- Collision avoidance with d3-force

### Analysis Tab
- Stage distribution bar charts
- Evolution chain summaries with time spans
- Top 6 most influential ideas ranked by score

### Predictions Tab
- Dormant idea detection with dormancy percentage scores
- Evolution forecasting with predicted next stage and confidence bars
- Visual confidence indicators (green > 70%, amber > 50%, red < 50%)

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool & dev server |
| Tailwind CSS | Styling |
| Framer Motion | Animations & transitions |
| Radix UI | Accessible component primitives |
| react-force-graph-2d | Force-directed graph visualization |
| d3-force | Graph physics simulation |
| @tanstack/react-query | Server state management |
| react-router-dom | Client-side routing |

---

## Running

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:8080)
npm run dev

# Production build
npm run build
```

> **Note:** The frontend expects the Flask backend running on `http://localhost:5000`. Start the backend first.
