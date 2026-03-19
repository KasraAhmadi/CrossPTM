# PTM Prediction API

A FastAPI-based REST service for predicting Post-Translational Modifications (PTMs) from protein sequences in FASTA format.

---

## Table of Contents

- [Docker Setup](#-docker-setup)
- [API Reference](#-api-reference)
- [PTM Types](#-ptm-types)
- [Examples](#-examples)
- [Response Format](#-response-format)
- [Error Codes](#-error-codes)

---

## 🐳 Docker Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system

### Build the Image

```bash
docker build -t ptm-prediction .
```

### Run the Container

```bash
docker run -p 8000:8000 ptm-prediction
```

The API will be available at `http://127.0.0.1:8000`.

### Dockerfile Configuration

Below is the Dockerfile used to build the image. Two common customizations are highlighted:

```dockerfile
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
```

#### 🔄 Changing the Model

Replace the model file referenced by `MODEL_PATH` and `COPY` with your new model:

```dockerfile
ENV MODEL_PATH=/app/models/your_new_model.pt
COPY ./models/your_new_model.pt /app/your_new_model.pt
```

#### ⚡ Enabling GPU Support

1. Change the `DEVICE` environment variable in the Dockerfile:

```dockerfile
ENV RUN_DEVICE=cuda
```

---

## 📡 API Reference

### `POST /predict`

Runs PTM site prediction on a protein sequence provided in FASTA format.

#### Endpoint

```
POST http://127.0.0.1:8000/predict
```

#### Headers

| Header         | Value              | Required |
|----------------|--------------------|----------|
| `Content-Type` | `application/json` | ✅ Yes   |

#### Request Body

| Field           | Type     | Required | Description                                          |
|-----------------|----------|----------|------------------------------------------------------|
| `fasta_content` | `string` | ✅ Yes   | Protein sequence in FASTA format (must include `>` header) |
| `ptm_type`      | `string` | ✅ Yes   | Type of PTM to predict. See [PTM Types](#-ptm-types) |

#### Request Schema

```json
{
  "fasta_content": "string",
  "ptm_type": "string"
}
```

---

## 🔬 PTM Types

The `ptm_type` field accepts the following values:

| Value                   | Modification Type          
|-------------------------|----------------------------
| `Phosphorylation_ST`    | Phosphorylation            
| `Phosphorylation_Y`     | Phosphorylation            
| `Ubiquitination_K`      | Ubiquitination             
| `Acetylation_K`         | Acetylation                
| `Methylation_R`         | Methylation                
| `NlinkedGlycosylation_N`| N-linked Glycosylation     
| `Methylation_K`         | Methylation                
| `Sumoylation_K`         | SUMOylation              

---

## 💡 Examples

### cURL

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/predict' \
  -H 'Content-Type: application/json' \
  -d '{
    "fasta_content": ">4EBP_DROME\nMSASPTARQAITQALPMITRKVVISDPIQMPEVYSSTPGGTLYSTTPGGTKLIYERAFMKNLRGSPLSQTPPSNVPSCLLRGTPRTPFRKCVPVPTELIKQTKSLKIEDQEQFQLDL",
    "ptm_type": "Phosphorylation_ST"
  }'
```

---

## 📤 Response Format

### Success Response

**Status Code:** `200 OK`

```json
{
  "status": "success",
  "results": [
    {
      "task": "Phosphorylation_ST",
      "prot_id": ["4EBP_DROME", "4EBP_DROME", "..."],
      "position": [4, 7, 21, "..."],
      "prediction": [0.923, 0.041, 0.876, "..."]
    }
  ]
}
```

#### Response Fields

| Field                    | Type            | Description                                                         |
|--------------------------|-----------------|---------------------------------------------------------------------|
| `status`                 | `string`        | `"success"` on a successful inference                               |
| `results`                | `array`         | List of result objects, one per prediction task                     |
| `results[].task`         | `string`        | The PTM task name corresponding to the request                      |
| `results[].prot_id`      | `array[string]` | Protein identifiers for each predicted site                         |
| `results[].position`     | `array[int]`    | 1-based residue positions of candidate PTM sites                    |
| `results[].prediction`   | `array[float]`  | Predicted probability scores (0–1) for each site                   |

> **Interpreting scores:** A `prediction` value closer to `1.0` indicates a higher confidence that the residue at that position is a PTM site.

---

## ❌ Error Codes

| HTTP Status | Detail Message                                      | Cause                                                  |
|-------------|-----------------------------------------------------|--------------------------------------------------------|
| `400`       | `Invalid FASTA: Missing header line starting with '>'` | The `fasta_content` field is missing the `>` header   |
| `500`       | `Inference failed: <error detail>`                  | An internal error occurred during model inference      |
| `503`       | `Model not loaded`                                  | The ML model failed to load on server startup          |