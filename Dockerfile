FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Expose port 7860 for Streamlit (default for Hugging Face Spaces; Render/Railway will also use this port because we expose it)
EXPOSE 7860

# Command to run the scripts together
CMD ["./start.sh"]
