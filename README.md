# Context Graph AI for SAP O2C

A graph-based data modeling and query system.

## Project Structure
- `src/`
  - `api/main.py`: FastAPI backend.
  - `core/`: Business logic (Graph, Query Engine).
  - `ui/app.py`: Streamlit frontend.
  - `ingest_data.py`: CLI for database setup.
- `sap-o2c-data/`: JSONL dataset.
- `sap_o2c.db`: SQLite database.

## Setup
1. Clone the repository and install requirements: `pip install -r requirements.txt`.
2. Set your `GROQ_API_KEY` in `.env`.
3. Ingest the data: `python src/ingest_data.py`.
4. **Start the Backend**: `uvicorn src.api.main:app --reload`.
5. **Start the Frontend**: `streamlit run src/ui/app.py`.

## Features
- End-to-end O2C flow visualization.
- Natural language queries with Dodge AI.
- Interactive graph sub-filtering.
