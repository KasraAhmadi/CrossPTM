import os
import yaml
import torch
import tempfile
import json
import uuid
import numpy as np
from datetime import datetime
from box import Box
from typing import List, Union, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from contextlib import asynccontextmanager
from types import SimpleNamespace

# Your project-specific imports
from utility.data import prepare_dataloaders_ptm
from utility.model import prepare_models_secondary_structure_ptm
from utility.test import predict

# --- CONFIGURATION ---
JOBS_DIR = "jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

ml_models = {}

# --- SCHEMAS ---
class InferenceRequest(BaseModel):
    user_id: str
    fasta_content: str
    ptm_type: Union[str, List[str]]

class JobStatusResponse(BaseModel):
    job_id: str
    user_id: str
    status: str
    created_at: str
    error: Optional[str] = None

# --- HELPERS ---
def get_job_path(job_id: str):
    return os.path.join(JOBS_DIR, f"{job_id}.json")

def save_job(job_data: dict):
    with open(get_job_path(job_data["job_id"]), "w") as f:
        json.dump(job_data, f)

def load_job(job_id: str) -> Optional[dict]:
    path = get_job_path(job_id)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

# --- BACKGROUND WORKER ---
def process_inference(job_id: str, fasta_content: str, ptm_types: List[str]):
    job = load_job(job_id)
    try:
        # 1. Update status to Running
        job["status"] = "Running"
        save_job(job)

        # 2. Extract model resources
        net = ml_models["net"]
        configs = ml_models["configs"]
        device = ml_models["device"]
        model_path = ml_models["model_path"]

        with tempfile.TemporaryDirectory() as temp_dir:
            fasta_path = os.path.join(temp_dir, 'input.fasta')
            with open(fasta_path, 'w') as f:
                f.write(fasta_content)
            
            ptm_task_results = []
            for ptm in ptm_types:
                args = SimpleNamespace(
                    data_path=fasta_path,
                    PTM_type=ptm,
                    save_path=temp_dir,
                    model_path=model_path
                )

                dataloaders_dict = prepare_dataloaders_ptm(args, configs)
                for task_name, dataloader in dataloaders_dict['test'].items():
                    prediction_results, _, position_results = predict(dataloader, net, device)
                    ptm_task_results.append({
                        "task": task_name,
                        "position": position_results,
                        "prediction": [float(p) for p in prediction_results]
                    })

        # 3. Success: Update job file
        job["status"] = "Finished"
        job["result"] = ptm_task_results
        job["finished_at"] = datetime.now().isoformat()
        save_job(job)

    except Exception as e:
        job["status"] = "Failed"
        job["error"] = str(e)
        save_job(job)

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    config_path = os.getenv("CONFIG_PATH", "./config/test.yaml")
    model_path = os.getenv("MODEL_PATH", "./models/model_1_0.pth")
    device = os.getenv("RUN_DEVICE", "cpu")

    with open(config_path) as file:
        configs = Box(yaml.full_load(file))

    net = prepare_models_secondary_structure_ptm(configs)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    net.load_state_dict(checkpoint['model_state_dict'])
    net.to(device)
    net.eval()

    ml_models.update({"net": net, "configs": configs, "device": device, "model_path": model_path})
    yield
    ml_models.clear()

app = FastAPI(lifespan=lifespan)

# --- ENDPOINTS ---

@app.post("/job", status_code=202)
async def create_job(request: InferenceRequest, background_tasks: BackgroundTasks):
    job_id = f"j_{uuid.uuid4().hex[:8]}"
    
    job_data = {
        "job_id": job_id,
        "user_id": request.user_id,
        "status": "Pending",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    save_job(job_data)

    ptm_types = [request.ptm_type] if isinstance(request.ptm_type, str) else request.ptm_type
    
    # Offload to background
    background_tasks.add_task(process_inference, job_id, request.fasta_content, ptm_types)
    
    return {"job_id": job_id, "status": "Pending"}

@app.get("/job/{job_id}/status", response_model=JobStatusResponse)
async def get_status(job_id: str):
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/job/{job_id}/result")
async def get_result(job_id: str):
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] in ["Pending", "Running"]:
        return {"status": job["status"], "message": "Job is still processing"}
    
    return job

@app.delete("/job/{job_id}")
async def delete_job(job_id: str, user_id: str = Query(...)):
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Ownership verification failed")
    
    if job["status"] in ["Finished", "Failed"]:
        # Requirement: Conflict if already in final state
        raise HTTPException(status_code=409, detail="Cannot cancel a completed job")

    os.remove(get_job_path(job_id))
    return {"message": "Job deleted"}