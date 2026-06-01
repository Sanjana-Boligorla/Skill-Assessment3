# ⚡ ProductIQ — AI-Powered Product Strategy Assistant

> A multi-agent AI system that transforms raw business data into actionable product strategy insights. Built with LangGraph, GPT-4o Mini, FastAPI, and a React + Tailwind CSS frontend — deployed with a single command.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Running the App](#running-the-app)
- [How to Use](#how-to-use)
- [Deploying to Render](#deploying-to-render)
- [Environment Variables](#environment-variables)
- [Sample Report](#sample-report)

---

## Overview

ProductIQ helps Product Managers make faster, data-driven decisions by processing uploaded business data through a pipeline of 7 specialized AI agents. Each agent focuses on a specific analytical lens and passes its findings to the next, building a comprehensive strategic picture.

**What it does:**
- Accepts CSV (sales data), PDF (market research), and TXT (feedback/surveys) uploads
- Runs 7 AI agents sequentially via LangGraph
- Generates 7 insight reports: Customer, Market, SWOT, Opportunities, Features, Strategy, Executive
- Renders an interactive dashboard with 8+ charts
- Produces a downloadable, professionally formatted PDF executive report
- Provides a natural language chat interface backed by all agent outputs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        STREAMLIT (app.py)                    │
│         Launches FastAPI thread + serves React UI            │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   FastAPI (api.py)       │
          │   REST endpoints:        │
          │   /upload-full  /run     │
          │   /status  /insights     │
          │   /chat    /report       │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   LangGraph Pipeline     │
          │                          │
          │  📥 Data Ingestion       │
          │       ↓                  │
          │  💬 Customer Feedback    │
          │       ↓                  │
          │  📊 Market Research      │
          │       ↓                  │
          │  🔲 SWOT Analysis        │
          │       ↓                  │
          │  🎯 Feature Priority     │
          │       ↓                  │
          │  🗺️  Strategy            │
          │       ↓                  │
          │  📋 Executive Report     │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │  React + Tailwind UI     │
          │  (frontend/index.html)   │
          │  served via              │
          │  st.components.v1.html   │
          └─────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Model | GPT-4o Mini (via key gateway) |
| Embeddings | text-embedding-3-small |
| Orchestration | LangGraph (DAG) |
| Vector DB | ChromaDB (Pinecone optional) |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + Tailwind CSS (CDN) |
| Charts | Chart.js |
| PDF Generation | ReportLab |
| App Server | Streamlit |
| Deployment | Render |

---

## Project Structure

```
product_strategy_assistant/
│
├── app.py                    # Entry point — launches FastAPI + React UI
├── api.py                    # FastAPI backend (all REST endpoints)
├── react_app.py              # Loads frontend/index.html, injects API URL
│
├── frontend/
│   └── index.html            # Full React + Tailwind app (CDN, no build step)
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py       # LangGraph DAG wiring + chat query
│   ├── data_ingestion.py     # Agent 1: parse & index files
│   ├── customer_feedback.py  # Agent 2: sentiment & review analysis
│   ├── market_research.py    # Agent 3: market trends & regional insights
│   ├── swot_analysis.py      # Agent 4: SWOT + opportunity scoring
│   ├── feature_prioritization.py  # Agent 5: ICE scoring & portfolio decisions
│   ├── strategy_recommendation.py # Agent 6: roadmap & action plan
│   └── executive_report.py   # Agent 7: executive summary + PDF metrics
│
├── utils/
│   ├── __init__.py
│   ├── data_parser.py        # CSV / PDF / TXT parsing
│   ├── vector_store.py       # ChromaDB / Pinecone abstraction
│   ├── pdf_generator.py      # ReportLab PDF builder (markdown-aware)
│   └── llm_client.py         # OpenAI client factory (gateway-aware)
│
├── requirements.txt
├── render.yaml               # Render deployment config
├── .env.example              # Environment variable template
├── .gitignore
└── Sample_Strategy_Report.pdf  # Sample generated report
```

---

## Local Setup

### Prerequisites
- Python 3.10+ (tested on 3.13)
- Git

### Step 1 — Clone the repo

```bash
git clone https://github.com/Sanjana-Boligorla/Skill-Assessment3.git
cd Skill-Assessment3
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create your `.env` file

```bash
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
```

Edit `.env`:

```env
OPENAI_API_KEY=learner052
OPENAI_BASE_URL=https://keygateway.arshnivlabs.com/v1
USE_PINECONE=false
```

> The app uses a key gateway at `keygateway.arshnivlabs.com` as a proxy to GPT-4o Mini. Set `OPENAI_API_KEY` to your learner key.

---

## Running the App

```bash
streamlit run app.py
```

The browser opens at `http://localhost:8501`. The app automatically starts a FastAPI server on port `8000` in a background thread — no separate command needed.

---

## How to Use

### 1. Upload Data
- Click the upload area and select one or more files:
  - **CSV** — sales data (Date, Product, Revenue, Profit, Rating, Reviews, etc.)
  - **PDF** — market research or competitor reports
  - **TXT** — survey responses or feature requests

### 2. Run Analysis
- Click **⚡ Run Full Analysis**
- Watch all 7 agents run live in the sidebar (dots animate as each agent runs)
- The progress bar fills as agents complete

### 3. Explore Results

| Tab | What you'll find |
|---|---|
| 📈 Dashboard | 8 interactive charts + KPI strip + product table |
| 🗂 Insights | 7 full AI-generated reports (Customer, Market, SWOT, etc.) |
| 💬 Chat | Ask natural language questions, get context-aware answers |
| 🏗 Architecture | Agent pipeline diagram, tech stack, deployment info |

### 4. Download the Report
- Click **📥 Download PDF** in the sidebar or Insights tab
- Get a professionally formatted multi-page PDF with cover page, metrics grid, table of contents, and all 7 reports

---

## Deploying to Render

### Step 1 — Push to GitHub
Your code is already at: `https://github.com/Sanjana-Boligorla/Skill-Assessment3`

### Step 2 — Create a Web Service on Render

1. Go to [render.com](https://render.com) and sign in
2. Click **New → Web Service**
3. Connect your GitHub account and select `Skill-Assessment3`
4. Configure:

| Setting | Value |
|---|---|
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |

### Step 3 — Add Environment Variables

In the Render dashboard under **Environment**:

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | `learner052` |
| `OPENAI_BASE_URL` | `https://keygateway.arshnivlabs.com/v1` |
| `USE_PINECONE` | `false` |

### Step 4 — Deploy

Click **Create Web Service**. Render will build and deploy automatically. Your live URL will be something like:
```
https://skill-assessment3.onrender.com
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your learner key (e.g. `learner052`) |
| `OPENAI_BASE_URL` | Yes | Gateway URL: `https://keygateway.arshnivlabs.com/v1` |
| `USE_PINECONE` | No | Set to `true` to use Pinecone instead of ChromaDB |
| `PINECONE_API_KEY` | If Pinecone | Your Pinecone API key |
| `PINECONE_INDEX_NAME` | If Pinecone | Index name (default: `product-strategy`) |

---

## Sample Report

A sample generated PDF report (`Sample_Strategy_Report.pdf`) is included in this repository. It was generated using the provided `Sample Sales Data.csv` and demonstrates all 7 agent outputs rendered in the PDF format.

---

## Evaluation Criteria Coverage

| Criteria | Weight | Implementation |
|---|---|---|
| Successful Deployment | 30% | Single-command Streamlit app, `render.yaml` config included |
| Quality of AI Insights | 35% | 7 specialized agents with role-specific system prompts, context chaining |
| Multi-Agent Design & UX | 35% | LangGraph DAG, live agent pipeline visibility, React dashboard, PDF report, chat Q&A |

### Bonus Features Implemented
- ✅ Advanced Multi-Agent Collaboration (agents share accumulated context)
- ✅ Product Opportunity Scoring (SWOT agent with scored opportunity matrix)
- ✅ Roadmap Generation (Now/Next/Later framework in Strategy agent)
- ✅ Interactive Dashboard (8 Chart.js visualizations)
- ✅ Executive Presentation Generation (PDF with cover, TOC, metrics grid)

---

## Agent Details

### Agent 1 — Data Ingestion
Parses uploaded files (CSV via pandas, PDF via pdfplumber, TXT via UTF-8 decode). Chunks text and indexes into ChromaDB using `text-embedding-3-small` for semantic search.

### Agent 2 — Customer Feedback
Analyzes product reviews and ratings. Identifies sentiment patterns, pain points, praise themes, and return rate signals per product and region.

### Agent 3 — Market Research
Evaluates category and regional performance, revenue velocity, marketing ROI, and pricing dynamics to surface market trends and competitive positioning signals.

### Agent 4 — SWOT Analysis
Synthesizes findings from Agents 2 and 3 into a structured SWOT (Strengths, Weaknesses, Opportunities, Threats) with a scored Product Opportunity Assessment (1–10 scale).

### Agent 5 — Feature Prioritization
Applies ICE scoring (Impact × Confidence ÷ Effort) to rank product improvements. Categorizes products into Invest / Optimize / Harvest decisions with resource allocation recommendations.

### Agent 6 — Strategy Recommendation
Generates a Strategic Action Plan (0–3 months, 3–6 months, 6–12 months) and Product Roadmap (Now / Next / Later) with success metrics and risk mitigation.

### Agent 7 — Executive Report
Distills all prior agent outputs into a board-ready Executive Summary with critical findings, top strategic priorities, decisions required, and 12-month outlook.

---

*Built for Skill Check Assessment 3 — AI-Powered Product Strategy Assistant*
