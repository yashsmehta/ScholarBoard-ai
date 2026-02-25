# 🧠 ScholarBoard.ai

**An interactive map of a scientific community — where every researcher is a dot, and nearby dots think alike.**

ScholarBoard.ai takes a roster of researchers, reads their publications with AI, and arranges them in 2D space by research similarity. The result is a living, explorable map of an entire field: clusters of related work, bridges between subfields, and a profile card for every scientist — complete with papers, subfield tags, and an AI-generated hypothesis for what they should work on next.

The current dataset: **~730 vision neuroscience researchers** from the [Vision Sciences Society (VSS)](https://www.visionsciences.org/).

---

## ✨ What you can do with it

- **Explore the landscape** — pan and zoom across the research map; clusters reveal the hidden structure of a field
- **Find neighbors** — see which researchers are working on the most similar problems
- **Discover someone new** — click any dot to read their bio, recent papers, and subfield tags
- **Get inspired** — each researcher has an AI-generated research direction: a novel hypothesis grounded in their actual work
- **Search by name or topic** — type a concept and get projected onto the map

---

## 🚀 Quickstart

**Prerequisites:** [uv](https://docs.astral.sh/uv/), Node.js 18+, a `GOOGLE_API_KEY` and `SERPER_API_KEY`

```bash
# 1. Install
git clone https://github.com/scienta-ai/ScholarBoard-ai.git
cd ScholarBoard-ai
uv sync
cd frontend && npm install && cd ..

# 2. Configure
echo "GOOGLE_API_KEY=..." >> .env
echo "SERPER_API_KEY=..." >> .env

# 3. Run the pipeline (builds everything from scratch)
uv run scripts/run_pipeline.py --execute

# 4. Launch
uv run serve.py &           # data server  → localhost:8000
cd frontend && npm run dev  # frontend      → localhost:5173
```

Open **http://localhost:5173** and start exploring.

---

## ⚙️ How it works

A fully automated, 8-step AI pipeline builds the map from a CSV of researcher names:

```
①  Papers      →  Gemini 3 Flash searches the web for each researcher's recent publications
②  Profiles    →  Gemini 3 Flash fetches their bio, institution, and lab URL
③  Embeddings  →  Gemini embeds each researcher's paper text into a 3072-dim vector
④  Map         →  UMAP reduces to 2D; HDBSCAN finds the clusters
⑤  Subfields   →  Cosine similarity maps each researcher to their closest research subfields
⑥  Ideas       →  Gemini 3.1 Pro (with extended thinking) proposes a novel research direction
⑦  Build       →  Everything is merged into a SQLite database, then exported to JSON
⑧  Pics        →  Serper.dev finds a headshot for each researcher
```

Check pipeline status at any time:

```bash
uv run scripts/run_pipeline.py          # show progress dashboard
uv run scripts/run_pipeline.py --step papers    # run one step
uv run scripts/run_pipeline.py --from embed     # resume from a step
```

---

## 🔬 Vision science subfields

Each researcher is automatically tagged across 23 subfields, from neural coding to perceptual learning:

> *Neural Coding · Representational Geometry · Brain-AI Alignment · Predictive Dynamics · Object Recognition · Face Perception · Scene Perception · Active Vision · Visuomotor Action · Attention · Visual Working Memory · Ensemble Statistics · Perceptual Learning · Multisensory Integration · Perceptual Decision-Making · Visual Development · Neural Decoding · Comparative Vision · Motion Perception · Color Vision · Visual Search · Reading & Word Recognition · Mid-Level Features*

---

## 🛠️ Stack

| What | How |
|---|---|
| AI pipeline | Google Gemini 3 Flash + 3.1 Pro + gemini-embedding-001 |
| Map layout | UMAP + HDBSCAN |
| Frontend | React 19 + TypeScript + D3.js |
| Data layer | SQLite + JSON + NetCDF (embeddings) |
| Package manager | `uv` (Python) · `npm` (frontend) |

---

## 📄 License

MIT
