import os
import yaml
import torch
import tempfile
import numpy as np
from box import Box
from time import time
from types import SimpleNamespace
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Your project-specific imports
from utility.data import prepare_dataloaders_ptm
from utility.model import prepare_models_secondary_structure_ptm
from utility.test import predict

# Global storage for the loaded model
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # 1. Get paths from environment variables (passed by Docker)
    config_path = os.getenv("CONFIG_PATH", "./config/test.yaml")
    model_path = os.getenv("MODEL_PATH", "./models/model_1_0.pth")
    device = os.getenv("RUN_DEVICE", "cpu")
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Loading configuration from: {config_path}")
    print(f"Loading model from: {model_path} on device: {device}")
    
    if not os.path.exists(model_path):
        raise RuntimeError(f"Model file not found at {model_path}")

    with open(config_path) as file:
        config_file = yaml.full_load(file)
    configs = Box(config_file)

    if isinstance(configs.fix_seed, int):
        torch.manual_seed(configs.fix_seed)
        np.random.seed(configs.fix_seed)

    # 2. Initialize and Load Weights
    net = prepare_models_secondary_structure_ptm(configs)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    net.load_state_dict(checkpoint['model_state_dict'])
    net.to(device)
    net.eval()

    ml_models["net"] = net
    ml_models["configs"] = configs
    ml_models["device"] = device
    ml_models["model_path"] = model_path # Save for reference in loaders
    
    yield
    # --- SHUTDOWN ---
    ml_models.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

class InferenceRequest(BaseModel):
    fasta_content: str
    ptm_type: str

@app.post("/predict")
async def run_inference(request: InferenceRequest):
    if "net" not in ml_models:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Use persistent model
    net = ml_models["net"]
    configs = ml_models["configs"]
    device = ml_models["device"]

    # Basic FASTA validation
    if ">" not in request.fasta_content:
        raise HTTPException(status_code=400, detail="Invalid FASTA: Missing header line starting with '>'")

    # Create temporary environment for this specific request
    with tempfile.TemporaryDirectory() as temp_dir:
        fasta_path = os.path.join(temp_dir, 'input.fasta')
        with open(fasta_path, 'w') as f:
            f.write(request.fasta_content)

        # Mock args for the existing dataloader function
        args = SimpleNamespace(
            data_path=fasta_path,
            PTM_type=request.ptm_type,
            save_path=temp_dir,
            model_path=ml_models["model_path"]
        )

        try:
            dataloaders_dict = prepare_dataloaders_ptm(args, configs)
            
            results = []
            for task_name, dataloader in dataloaders_dict['test'].items():
                prediction_results, prot_id_results, position_results = predict(dataloader, net, device)
                
                results.append({
                    "task": task_name,
                    "prot_id": prot_id_results,
                    "position": position_results,
                    # Convert numpy/tensor to list for JSON
                    "prediction": [float(p) for p in prediction_results] 
                })

            return {
                "status": "success",
                "results": results,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")