FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- New: Default Environment Variables ---
ENV MODEL_PATH=/app/model_1_0.pth
ENV CONFIG_PATH=/app/config/test.yaml
ENV TORCH_HOME=/app/.cache/torch
ENV RUN_DEVICE=cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./models/model_1_0.pth /app/model_1_0.pth
COPY . .

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]