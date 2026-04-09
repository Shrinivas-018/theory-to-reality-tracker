# Theory-to-Reality Evolution Tracker

Track how ideas evolve from philosophical concepts to modern technology.
Built with Flask, React, NetworkX, Interval Trees, Segment Trees, and Google Gemini AI.

## Features

- Search-driven idea exploration (no data overload)
- Evolution timeline: Philosophy → Science → Engineering → Technology
- Interactive lineage graph showing idea influence networks
- AI-powered descriptions using Google Gemini
- Dormant idea detection and innovation predictions
- Export dataset as CSV or JSON

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, NetworkX |
| Data Structures | Interval Tree, Segment Tree |
| ML | TF-IDF, Cosine Similarity |
| AI | Google Gemini API |
| Frontend | React, TypeScript, Tailwind CSS, Vite |
| Data Source | OpenAlex Scholarly API |

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/theory-to-reality-tracker.git
cd theory-to-reality-tracker
```

### 2. Install Python dependencies
```bash
pip install flask flask-cors pandas networkx scikit-learn python-dotenv google-genai
```

### 3. Set your Gemini API key
Create a `.env` file in the root:
```
GEMINI_API_KEY=your_key_here
```
Get a free key at https://aistudio.google.com/

### 4. Fetch the dataset
```bash
python -m backend.scripts.fetch_openalex
```

### 5. Start the backend
```bash
python -m backend.api
```

### 6. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 7. Open in browser
- Frontend: http://localhost:8080
- API: http://localhost:5000

## Usage

1. Type any keyword in the search box (e.g. "quantum", "DNA", "gravity")
2. Filter by evolution stage or category
3. Click **AI Summarize** on any idea card for a Gemini-generated description
4. Switch to **Lineage Graph** tab to see idea connections visually
5. Check **Predictions** tab for dormant ideas with innovation potential
