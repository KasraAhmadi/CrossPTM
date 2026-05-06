# PTM Prediction API (Asynchronous)

A FastAPI-based REST service for predicting Post-Translational Modifications (PTMs) from protein sequences. This version uses an asynchronous background processing system suitable for long-running ML tasks.

---

## Table of Contents

- [Job Lifecycle](#-job-lifecycle)
- [API Reference](#-api-reference)
- [PTM Types](#-ptm-types)
- [Docker Setup](#-docker-setup)
- [Error Codes](#-error-codes)

---

## 🔄 Job Lifecycle

Since ML inference can be time-consuming, this API uses a **Submit → Poll → Fetch** pattern:

1. **Submit**  
   Client `POST`s a job and receives a `job_id`.

2. **Poll**  
   Client checks `/job/{job_id}/status` periodically.

3. **Fetch**  
   Once the status is `Finished`, the client retrieves the full result from `/job/{job_id}/result`.

---

# 📡 API Reference

## 1. Submit a Job

### `POST /job`

Starts a background inference task.

Returns a `202 Accepted` status.

### Request Body

```json
{
  "user_id": "unique_client_session_id",
  "fasta_content": ">Header\nMSASPTAR...",
  "ptm_type": ["Phosphorylation_ST"]
}
```

---

## 2. Check Job Status

### `GET /job/{job_id}/status`

Returns the current state of the job.

### Status Values

- `Pending` — Waiting in queue
- `Running` — Model is currently processing
- `Finished` — Processing complete
- `Failed` — An error occurred

---

## 3. Get Result

### `GET /job/{job_id}/result`

Returns the full job record.

If the job is `Finished`, the `result` field will contain the prediction data.

---

## 4. Delete Job

### `DELETE /job/{job_id}?user_id={user_id}`

Cancels and removes a job from the server.

Only allowed if the job is not yet in a final state (`Finished` / `Failed`).

---

# 🔬 PTM Types

The `ptm_type` field accepts the following values:

| Value | Modification Type |
|---|---|
| `Phosphorylation_ST` | Phosphorylation |
| `Phosphorylation_Y` | Phosphorylation |
| `Ubiquitination_K` | Ubiquitination |
| `Acetylation_K` | Acetylation |
| `Methylation_R` | Methylation |
| `NlinkedGlycosylation_N` | N-linked Glycosylation |
| `Methylation_K` | Methylation |
| `Sumoylation_K` | SUMOylation |

---

# 💡 Example Workflow (cURL)

## Step 1: Submit Job

```bash
curl -X 'POST' 'http://127.0.0.1:8000/job' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "browser_user_1",
    "fasta_content": ">4EBP_DROME\nMSASPTAR...",
    "ptm_type": ["Phosphorylation_ST"]
  }'
```

### Returns

```json
{
  "job_id": "j_abc123",
  "status": "Pending"
}
```

---

## Step 2: Poll Status

```bash
curl -X 'GET' 'http://127.0.0.1:8000/job/j_abc123/status'
```

---

## Step 3: Fetch Results

```bash
curl -X 'GET' 'http://127.0.0.1:8000/job/j_abc123/result'
```

---

# 📤 Response Format (Finished Job)

```json
{
  "job_id": "j_abc123",
  "user_id": "browser_user_1",
  "status": "Finished",
  "result": [
    {
      "task": "Phosphorylation_ST",
      "position": [2, 4, 6],
      "prediction": [0.986, 0.998, 0.895]
    }
  ],
  "created_at": "2026-05-06T19:44:52",
  "finished_at": "2026-05-06T19:45:02"
}
```

---

# 🐳 Docker Setup

## Build the Image

```bash
docker build -t ptm-prediction .
```

---

## Run the Container

```bash
docker run -p 8000:8000 ptm-prediction
```

---

# ❌ Error Codes

| HTTP Status | Detail Message | Cause |
|---|---|---|
| `403` | Ownership verification failed | Provided `user_id` does not match the job owner |
| `404` | Job not found # PTM Prediction API (Asynchronous)

A FastAPI-based REST service for predicting Post-Translational Modifications (PTMs) from protein sequences. This version uses an **asynchronous background processing system** to handle long-running ML tasks without blocking the server or timing out the client.

---

## 🔄 Job Lifecycle

Since ML inference involves heavy computation, this API follows an asynchronous **Submit-Poll-Fetch** pattern:

1.  **Submit**: Client POSTs data and receives a unique `job_id`.
2.  **Poll**: Client checks `/job/{job_id}/status` at regular intervals (e.g., every 5 seconds).
3.  **Fetch**: Once status is `Finished`, the client retrieves results from `/job/{job_id}/result`.

---

## 📡 API Reference

### 1. Submit a Job
`POST /job`
Starts a background inference task. Returns a `202 Accepted` status.

**Request Body:**
```json
{
  "user_id": "session_uuid_generated_by_frontend",
  "fasta_content": ">Protein_Name\nMSASPTARQAITQAL...",
  "ptm_type": ["Phosphorylation_ST", "Acetylation_K"]
}| The `job_id` does not exist in the `jobs/` directory |
| `409` | Cannot cancel a completed job | Attempted to `DELETE` a job that is already `Finished` or `Failed` |
| `503` | Model not loaded | The ML model failed to initialize during server lifespan |
