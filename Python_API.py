# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import time

app = FastAPI()

# Allow any frontend to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["https://yourwebsite.com"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track metrics file
metrics_file = "apm_metrics.json"

def log_metric(data):
    with open(metrics_file, "a") as file:
        file.write(json.dumps(data) + "\n")

# Middleware to track all API calls
@app.middleware("http")
async def track_api_performance(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # milliseconds

    metric = {
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": round(process_time, 2),
        "client_ip": request.client.host,
    }
    log_metric(metric)
    return response

# Custom APM event tracking endpoint
@app.post("/apm/track_event/")
async def track_event(event: dict):
    event["timestamp"] = datetime.utcnow().isoformat()
    log_metric(event)
    return {"status": "success", "message": "Event tracked"}
