# Context Graph AI for SAP O2C

[![Live Demo](https://img.shields.io/badge/Live_Demo-contextgraphai.onrender.com-success?style=for-the-badge)](https://contextgraphai.onrender.com)

A sophisticated graph-based data modeling and natural language query system designed to unify fragmented SAP Order-to-Cash (O2C) data.

## Project Structure
- `src/`
  - `api/main.py`: FastAPI backend exposing graph data and query endpoints with strict Pydantic validation.
  - `core/`: Core business logic containing `GraphManager` (NetworkX) and `QueryEngine` (LLM integration).
  - `ui/app.py`: Streamlit frontend featuring an interactive physics-based graph and a Dodge AI chat interface.
  - `ingest_data.py`: CLI script for robust JSONL-to-SQLite data ingestion.
- `sap-o2c-data/`: Source JSONL datasets representing SAP tables.
- `sap_o2c.db`: Relational SQLite database.

## Architecture & Design Decisions

### 1. Database Choice: SQLite as ingestion layer
While the end goal is a graph, directly building an in-memory graph from massive, fragmented JSONL files is memory-intensive and error-prone. We chose **SQLite** as an intermediate relational layer because:
- **Structure & Relationships**: It naturally handles the tabular nature of the raw SAP exports, allowing us to query and join tables efficiently before graph construction.
- **Performance**: Fetching a specific order's footprint (Order -> Delivery -> Billing -> Accounting) is significantly faster using indexed SQL queries compared to traversing raw JSON.
- **Portability**: It requires no separate server setup, aligning with the project's embedded goals.

### 2. Microservices Architecture: FastAPI + Streamlit
The application evolved from a monolithic script into a client-server model:
- **FastAPI** provides a robust, strictly-typed (via Pydantic) REST API, decoupling the heavy graph and LLM logic from the UI.
- **Streamlit** handles the frontend, rendering the Pyvis Network graph and chat UI. This separation ensures scalability and easier deployment (e.g., using Docker).

## LLM Strategy & Guardrails

### Prompting Strategy
The system uses **Groq (Llama 3.1 8b)** for rapid, cost-effective inference. To ensure factual accuracy ("Context Graphing"), we use a **Data Grounding Strategy**:
1. **Dynamic Subgraph Extraction**: When a user queries a document (e.g., "Status of Order 740506"), the system searches the graph and extracts *only* the relevant connected nodes and their attributes.
2. **Context Injection**: This subgraph data is formatted as JSON and injected directly into the LLM's system prompt.
3. **Instruction**: The LLM is explicitly instructed to act as "Dodge AI" and answer *strictly* using the provided JSON context.

### Guardrails
To prevent hallucinations and out-of-domain answers, robust guardrails are implemented:
- **Entity Detection**: The `QueryEngine` uses regex to actively search for SAP document IDs (6-10 digits) in the user's prompt.
- **Context Limitation**: If no relevant IDs are found, or the requested document doesn't exist in the database, the LLM is programmatically forced to decline the query gracefully.
- **Domain Restriction**: The system prompt explicitly forbids the LLM from answering general knowledge questions (e.g., "Who won the World Cup?") by confining its persona entirely to the provided SAP O2C data.

## Setup & Execution

### Local Setup
1. Clone the repository and install requirements: `pip install -r requirements.txt`.
2. Set your `GROQ_API_KEY` in a `.env` file at the root.
3. Ingest the data: `python src/ingest_data.py`.

### Running Locally
4. **Start the Backend**: `uvicorn src.api.main:app --reload` (Runs on port 8000)
5. **Start the Frontend**: `streamlit run src/ui/app.py` (Runs on port 8501)

### Docker Deployment
The system can be containerized using the provided `Dockerfile` and `start.sh` script to run both the FastAPI backend and Streamlit frontend concurrently.

## Features
- **End-to-end O2C Visualization**: Trace the entire lifecycle from Customer -> Sales Order -> Delivery -> Billing -> Payment.
- **Dodge AI Chat**: Human-friendly insights backed by strict graph data.
- **Interactive Graph Sub-filtering**: The graph dynamically filters to focus on specific queried documents, maintaining a clean UI.
