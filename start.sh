# Start the FastAPI backend in the background
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit frontend in the foreground
streamlit run src/ui/app.py --server.port 7860 --server.address 0.0.0.0
