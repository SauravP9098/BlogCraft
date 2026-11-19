# BlogCraft ✍️⚡
### Autonomous Multi-Agent Technical Blog Generation Platform

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![AWS](https://img.shields.io/badge/Cloud-AWS%20(Bedrock%20%7C%20S3%20%7C%20EC2%20%7C%20ECR)-232F3E.svg)](https://aws.amazon.com/)
[![VectorDB](https://img.shields.io/badge/VectorDB-Pinecone-teal.svg)](https://www.pinecone.io/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20(Render)-4169E1.svg)](https://render.com/)
[![Observability](https://img.shields.io/badge/Observability-GlassFlow%20Rius-8A2BE2.svg)](https://glassflow.dev/)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED.svg)](https://www.docker.com/)

---

## 📖 Table of Contents
- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [The Production Stack](#-the-production-stack)
- [How I Built This: Step-by-Step Engineering Journey](#-how-i-built-this-step-by-step-engineering-journey)
  - [Step 1: Graph State Machine & Agent Router](#step-1-graph-state-machine--agent-router)
  - [Step 2: Temporal Grounding & Tavily Research Engine](#step-2-temporal-grounding--tavily-research-engine)
  - [Step 3: Dynamic Outlining & Parallel Worker Fan-Out](#step-3-dynamic-outlining--parallel-worker-fan-out)
  - [Step 4: Reducer Subgraph, Image Planning & Diagram Synthesis](#step-4-reducer-subgraph-image-planning--diagram-synthesis)
  - [Step 5: Cloud Storage & Vector Memory (S3 + Pinecone)](#step-5-cloud-storage--vector-memory-s3--pinecone)
  - [Step 6: Relational Persistence & Live Telemetry (Render + GlassFlow)](#step-6-relational-persistence--live-telemetry-render--glassflow)
  - [Step 7: Designing the Studio Web UI](#step-7-designing-the-studio-web-ui)
  - [Step 8: Dockerization, ECR, EC2 & GitHub Actions CI/CD](#step-8-dockerization-ecr-ec2--github-actions-cicd)
- [Directory Layout](#-directory-layout)
- [Local Setup & Getting Started](#-local-setup--getting-started)
- [API Reference](#-api-reference)
- [Deployment Walkthrough](#-deployment-walkthrough)
- [License](#-license)

---

## 💡 Overview

Writing a comprehensive, publication-grade technical blog post is hard. It demands hours of domain research, verifying code syntax, selecting credible reference citations, organizing an outline with appropriate depth, drafting clean prose, and illustrating core concepts with diagrams.

**BlogCraft** is an autonomous multi-agent engineering platform designed to automate this entire lifecycle. Rather than relying on a single monolithic prompt, BlogCraft orchestrates an ensemble of specialized agents via **LangGraph**:
1. **Classifying** topic novelty and recency windows.
2. **Synthesizing** authoritative live web evidence.
3. **Structuring** a 5–9 section blueprint with strict word targets.
4. **Drafting** markdown sections concurrently in parallel.
5. **Harmonizing** the assembled draft, calculating image placements, and generating contextual architecture diagrams.

The result is a production-ready system backed by **Amazon Bedrock**, **Pinecone**, **PostgreSQL on Render**, **Amazon S3**, **GlassFlow Rius telemetry**, and a responsive **FastAPI + Vanilla Web Studio**.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph UserInterface["Client Layer"]
        UI["Studio Web UI (HTML/CSS/JS)"]
        API["FastAPI REST Server (:8000)"]
        UI <-->|JSON / SSE| API
    end

    subgraph LangGraphEngine["Multi-Agent Orchestration (LangGraph)"]
        START((START)) --> Router["🧭 Router Node<br/>(Decide Mode & Research Need)"]
        
        Router -->|needs_research = true| Research["🔍 Research Node<br/>(Tavily Search API)"]
        Router -->|needs_research = false| Orchestrator["📋 Orchestrator Node<br/>(Plan Outline & Section Tasks)"]
        
        Research --> Orchestrator
        
        Orchestrator -->|"LangGraph Send() Fan-Out"| W1["⚡ Worker 1"]
        Orchestrator -->|"LangGraph Send() Fan-Out"| W2["⚡ Worker 2"]
        Orchestrator -->|"LangGraph Send() Fan-Out"| WN["⚡ Worker N"]
        
        subgraph ReducerSubgraph["Reducer Subgraph"]
            direction TB
            Merge["🔗 merge_content<br/>(Sort by ID & Join)"] --> Decide["🖼️ decide_images<br/>(Placement & Prompts)"]
            Decide --> GenImages["🎨 generate_and_place_images<br/>(Image Synthesis & S3 Upload)"]
        end

        W1 --> ReducerSubgraph
        W2 --> ReducerSubgraph
        WN --> ReducerSubgraph
        
        ReducerSubgraph --> END_((END))
    end

    subgraph StorageCloud["Data, Cloud & Observability Layer"]
        Bedrock["AWS Bedrock<br/>(Claude 3.5 Sonnet / Haiku / Titan)"]
        Pinecone["Pinecone Vector DB<br/>(Semantic Memory & RAG)"]
        S3["Amazon S3<br/>(Articles & Rendered Diagrams)"]
        Postgres["PostgreSQL (Render)<br/>(Jobs, State, Metadata)"]
        GlassFlow["GlassFlow Rius<br/>(Agent Traces & Token Metrics)"]
    end

    API --> LangGraphEngine
    Router -.-> Bedrock
    Orchestrator -.-> Bedrock
    W1 & W2 & WN -.-> Bedrock
    Decide -.-> Bedrock
    GenImages -.-> S3
    LangGraphEngine -.-> Postgres
    LangGraphEngine -.-> Pinecone
    LangGraphEngine -.-> GlassFlow
```

---

## 🛠️ The Production Stack

| Component | Technology | Rationale |
|---|---|---|
| **Agentic Framework** | **LangGraph (`StateGraph`)** | Cyclic state graphs, fine-grained state reduction (`operator.add`), dynamic fan-out via `Send()`, and nested subgraphs. |
| **Foundation LLM** | **Amazon Bedrock** (`Claude 3.5 Sonnet` & `Haiku`) | Enterprise SLA, zero data-retention guarantees, and structured JSON output. |
| **Image Generation** | **Amazon Titan Image Generator v2** / **Gemini** | Programmatic synthesis of technical diagrams and illustrations. |
| **Vector Database** | **Pinecone (Serverless)** | High-throughput semantic memory, article deduplication, and past-context retrieval. |
| **Object Storage** | **Amazon S3** | Durable storage for generated Markdown manuscripts and rendered diagram images. |
| **Relational Database** | **PostgreSQL on Render** | ACID-compliant storage for blog generation runs, user history, audit logs, and status queues. |
| **Observability** | **GlassFlow & Rius** | Streaming event telemetry, agent execution latencies, and token cost monitoring. |
| **Web Studio** | **HTML5 / CSS3 / ES6 JavaScript** | Zero-dependency, lightweight, high-performance UI featuring a real-time multi-agent pipeline stepper. |
| **API Backend** | **FastAPI + Uvicorn** | Asynchronous HTTP endpoints, Pydantic v2 data validation, and static asset serving. |
| **Container & Cloud** | **Docker + Amazon ECR + Amazon EC2** | Reproducible containerized builds pushed to ECR and hosted on a cost-effective EC2 instance. |
| **CI/CD** | **GitHub Actions** | Automated linting, test suites, container builds, and deployment via SSH keys. |

---

## 🚀 How I Built This: Step-by-Step Engineering Journey

Here is the step-by-step breakdown of how this project evolved from a prototype script into a production-grade multi-agent architecture:

### Step 1: Graph State Machine & Agent Router
I began by replacing brittle prompt chains with a typed state machine powered by **LangGraph**. 
- Created `State` as a typed dictionary carrying inputs, router decisions, research evidence, section tuples, and the finished markdown.
- Built `router_node` utilizing structured outputs (`RouterDecision`). Instead of treating every query the same, the router inspects the topic and as-of date to categorize requests into:
  - `closed_book`: Evergreen technical concepts (e.g., *Self-attention mechanisms*). Skips web search to avoid latency and hallucinations.
  - `hybrid`: Foundational concepts that require up-to-date real-world tools or frameworks (e.g., *State of LangGraph in 2026*).
  - `open_book`: Fast-moving news, policy updates, and release roundups requiring strict recent citations.

### Step 2: Temporal Grounding & Tavily Research Engine
To prevent outdated citations, I built `research_node`:
- Connects to the **Tavily Search API**, pulling up to 10 scoped, high-signal technical queries.
- Normalizes search snippets into structured `EvidenceItem` objects.
- Implemented **Temporal Anchoring**: uses an `as_of` date with dynamic recency cutoff windows:
  $$\text{Cutoff} = \text{as\_of} - \text{recency\_days}$$
  - `open_book`: 7-day cutoff.
  - `hybrid`: 45-day cutoff.
  - `closed_book`: Evergreen (up to 10 years).
- Any source published before the cutoff or with an invalid URL is filtered out.

### Step 3: Dynamic Outlining & Parallel Worker Fan-Out
One model attempting to write a 3,000-word technical post in a single shot suffers from context degradation and lazy prose. 
- The **Orchestrator Node** acts as the lead editor: it ingests the gathered evidence and produces a validated `Plan` containing 5 to 9 granular `Task` items. Each task defines a strict goal, target word count (150–550 words), ordered bullet points, and flags (`requires_code`, `requires_citations`).
- **Parallel Fan-Out**: Using LangGraph's `Send()` primitive, the orchestrator spawns independent `worker_node` instances concurrently.
- Configured the state reducer on `sections` with `operator.add`:
  ```python
  sections: Annotated[List[tuple[int, str]], operator.add]
  ```
  This allows parallel workers to append their `(task_id, section_markdown)` tuples asynchronously without race conditions or overwriting.

### Step 4: Reducer Subgraph, Image Planning & Diagram Synthesis
Once all parallel workers finish, execution routes to a compiled **Reducer Subgraph**:
1. `merge_content`: Sorts sections by `task.id`, guarantees sequence integrity, and attaches the primary `# H1` header.
2. `decide_images`: An editor LLM scans the unified draft and pinpoints strategic locations for technical diagrams (capped at 3). It inserts explicit `[[IMAGE_1]]`, `[[IMAGE_2]]` tokens and creates detailed visual prompts.
3. `generate_and_place_images`: Dispatches prompts to the image generation engine (Amazon Titan / Gemini), writes images to disk/S3, and replaces tokens with formatted Markdown links. If image generation experiences an API blip, it safely degrades into an informative blockquote fallback rather than crashing the pipeline.

### Step 5: Cloud Storage & Vector Memory (S3 + Pinecone)
To make the architecture cloud-native and decouple storage from compute:
- **Amazon S3**: Integrated `boto3` to stream finalized markdown articles and generated images directly into an S3 bucket (`outputs/blogs/` and `outputs/images/`), served globally via CloudFront or pre-signed URLs.
- **Pinecone**: Added vector index indexing for generated blogs and source evidence chunks. This enables semantic deduplication, cross-article referencing, and context-aware RAG for future articles.

### Step 6: Relational Persistence & Live Telemetry (Render + GlassFlow)
- **PostgreSQL on Render**: Set up a managed database using connection pooling (`psycopg[pool]`) to record every generation request, user parameters, router modes, generated tokens, and file references.
- **GlassFlow & Rius**: Integrated real-time streaming telemetry into each agent step. Captures token usage, node execution latency, error boundaries, and provides end-to-end tracing across the LangGraph state transitions.

### Step 7: Designing the Studio Web UI
Built a dedicated, responsive developer studio in `frontend/`:
- **Interactive Studio Form**: Clean topic input, inspiration chips, and an As-Of Date picker.
- **Multi-Agent Pipeline Stepper**: A live visual stepper reflecting the backend execution flow in real-time (Router &rarr; Tavily &rarr; Orchestrator &rarr; Parallel Workers &rarr; Reducer) with an elapsed timer and agent ticker.
- **Rendered Reading Experience**: Full markdown typography, syntax-highlighted code with one-click copy buttons, clickable image lightboxes, and an auto-generated Table of Contents (TOC) sidebar.
- **Export & History**: LocalStorage persistence, instant Markdown copy, `.md` file download, and clean PDF print styling.

### Step 8: Dockerization, ECR, EC2 & GitHub Actions CI/CD
To finalize production readiness:
- Authored a multi-stage `Dockerfile` minimizing image size and optimizing caching layers.
- Configured a **GitHub Actions** workflow (`.github/workflows/deploy.yml`):
  1. Triggers on push to `main`.
  2. Runs pytest automated test suites.
  3. Builds Docker container and authenticates to **Amazon ECR**.
  4. Pushes container image with Git commit SHA tags.
  5. Connects via SSH to **Amazon EC2**, pulls the new image, runs migrations, and restarts containers via zero-downtime rolling restart.

---

## 📂 Directory Layout

```
blog-writing-agent/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline
├── backend/
│   ├── api/
│   │   ├── main.py             # FastAPI entrypoint, routes, static mounts
│   │   └── __init__.py
│   ├── config.py               # Central config, models, recency limits, paths
│   ├── graph/
│   │   ├── main_graph.py       # Compiled primary LangGraph pipeline
│   │   ├── reducer_graph.py    # Subgraph for merge & image synthesis
│   │   └── __init__.py
│   ├── llm.py                  # LLM client setup (Amazon Bedrock / OpenAI)
│   ├── nodes/
│   │   ├── orchestrator.py     # Outline generation & fan-out logic
│   │   ├── reducer.py          # Merging, image planning, file saving
│   │   ├── research.py         # Tavily search & recency filtration
│   │   ├── router.py           # Mode classification & search routing
│   │   ├── worker.py           # Single section technical writer
│   │   └── __init__.py
│   ├── prompts/                # Individual prompt templates per node
│   ├── schemas/                # Pydantic v2 data models & State TypedDict
│   ├── tools/
│   │   ├── gemini_image.py     # Image generation adapter
│   │   ├── tavily_search.py    # Web search adapter
│   │   └── __init__.py
│   └── utils/                  # Safe slugs, date parsing, filesystem helpers
├── frontend/
│   ├── index.html              # Studio interface & agent stepper
│   ├── style.css               # Modern dark/light theme, typography, print styles
│   └── app.js                  # Client logic, marked.js, TOC parser, history
├── outputs/
│   ├── blogs/                  # Generated markdown articles
│   └── images/                 # Rendered visual diagrams
├── tests/                      # Pytest unit & integration test suites
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Local multi-container orchestration
├── pyproject.toml              # UV / PEP 621 package metadata
├── requirements.txt            # Locked pip dependencies
└── README.md                   # This documentation
```

---

## 💻 Local Setup & Getting Started

### 1. Prerequisites
- Python 3.13+ (or [uv](https://github.com/astral-sh/uv))
- Git
- AWS Account (with Bedrock model access enabled)

### 2. Clone & Environment Configuration
```bash
git clone https://github.com/SauravP9098/blog-writing-agent.git
cd blog-writing-agent
```

Create your virtual environment:
```bash
# Using standard venv
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Or using uv
uv venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
# Or: uv pip install -r requirements.txt
```

Create and configure your `.env`:
```bash
cp .env.example .env
```

Populate the keys in `.env`:
```dotenv
# AWS Bedrock & S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
S3_BUCKET_NAME=your-s3-bucket-name

# Pinecone Vector DB
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=blogcraft-index

# PostgreSQL on Render
DATABASE_URL=postgresql://user:password@host.oregon-postgres.render.com/dbname

# Observability
RIUS_API_KEY=your-glassflow-rius-key

# Search & Tools
TAVILY_API_KEY=your-tavily-key
```

### 3. Launch the Server
```bash
uvicorn backend.api.main:api --reload --port 8000
```

Open your browser:
- **Studio Interface**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Reference

### Generate a Blog Post
```http
POST /generate
Content-Type: application/json
```

#### Request Payload
```json
{
  "topic": "Deep dive into Transformers and Self-Attention mechanisms",
  "as_of": "2026-11-19"
}
```

#### Response (200 OK)
```json
{
  "title": "Understanding Self-Attention in Transformers from First Principles",
  "mode": "closed_book",
  "needs_research": false,
  "queries": [],
  "evidence": [],
  "markdown": "# Understanding Self-Attention in Transformers...\n\n## The Intuition Behind Attention\n..."
}
```

---

## 🚢 Deployment Walkthrough

### 1. Docker Build & Local Run
```bash
docker build -t blog-writing-agent:latest .
docker run -p 8000:8000 --env-file .env blog-writing-agent:latest
```

### 2. Push to Amazon ECR
```bash
# Authenticate Docker to your Amazon ECR registry
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag blog-writing-agent:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/blogcraft:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/blogcraft:latest
```

### 3. Continuous Deployment with GitHub Actions
Configure the following secrets in GitHub Repository Settings:
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY`
- `EC2_HOST` (Public IP of EC2)
- `EC2_USER` (e.g., `ubuntu`)
- `EC2_SSH_KEY` (Private SSH Key)

On every `git push origin main`, the automated CI/CD pipeline builds, tests, pushes the image to ECR, and deploys it cleanly to your EC2 instance.

---

## 📄 License
Distributed under the **Apache 2.0 License**. See [LICENSE](LICENSE) for more details.

---
**Crafted with care by [Saurav Pawar](https://github.com/SauravP9098)**.
