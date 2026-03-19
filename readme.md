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
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ⬇️  Replace this path with your own model file if you swap models
ENV MODEL_PATH=/app/models/your_model.pt

# ⬇️  Change 'cpu' to 'cuda' here if you want to run on GPU
ENV DEVICE=cpu

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 🔄 Changing the Model

Replace the model file referenced by `MODEL_PATH` with your new model:

```dockerfile
ENV MODEL_PATH=/app/models/your_new_model.pt
```

Or mount a model from your host machine at runtime:

```bash
docker run -p 8000:8000 -v /path/to/your/model.pt:/app/models/your_model.pt ptm-prediction
```

#### ⚡ Enabling GPU Support

1. Ensure you have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed.
2. Change the `DEVICE` environment variable in the Dockerfile:

```dockerfile
ENV DEVICE=cuda
```

3. Run with GPU access:

```bash
docker run --gpus all -p 8000:8000 ptm-prediction
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

| Value                   | Modification Type          | Target Residue |
|-------------------------|----------------------------|----------------|
| `Phosphorylation_ST`    | Phosphorylation            | Serine / Threonine (S/T) |
| `Phosphorylation_Y`     | Phosphorylation            | Tyrosine (Y)   |
| `Ubiquitination_K`      | Ubiquitination             | Lysine (K)     |
| `Acetylation_K`         | Acetylation                | Lysine (K)     |
| `Methylation_R`         | Methylation                | Arginine (R)   |
| `NlinkedGlycosylation_N`| N-linked Glycosylation     | Asparagine (N) |
| `Methylation_K`         | Methylation                | Lysine (K)     |
| `Sumoylation_K`         | SUMOylation                | Lysine (K)     |

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

### Python (requests)

```python
import requests

url = "http://127.0.0.1:8000/predict"

payload = {
    "fasta_content": ">4EBP_DROME\nMSASPTARQAITQALPMITRKVVISDPIQMPEVYSSTPGGTLYSTTPGGTKLIYERAFMKNLRGSPLSQTPPSNVPSCLLRGTPRTPFRKCVPVPTELIKQTKSLKIEDQEQFQLDL",
    "ptm_type": "Phosphorylation_ST"
}

response = requests.post(url, json=payload)
print(response.json())
```

### JavaScript (fetch)

```javascript
const response = await fetch("http://127.0.0.1:8000/predict", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    fasta_content: ">4EBP_DROME\nMSASPTARQAITQALPMITRKVVISDPIQMPEVYSSTPGGTLYSTTPGGTKLIYERAFMKNLRGSPLSQTPPSNVPSCLLRGTPRTPFRKCVPVPTELIKQTKSLKIEDQEQFQLDL",
    ptm_type: "Phosphorylation_ST"
  })
});

const data = await response.json();
console.log(data);
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