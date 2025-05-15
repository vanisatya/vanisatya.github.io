from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from datetime import datetime
import json
import time
import os

app = FastAPI()

# Allow any frontend to call your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your website URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create logs folder
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
metrics_file = os.path.join(log_folder, "apm_metrics.log")
contact_file = os.path.join(log_folder, "contact_form_submissions.log")

def log_metric(data):
    data["logged_at"] = datetime.utcnow().isoformat()
    with open(metrics_file, "a") as file:
        file.write(json.dumps(data) + "\n")

# ➡️ Middleware: Track all API requests
@app.middleware("http")
async def track_api_performance(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        error_metric = {
            "type": "exception",
            "error": str(e),
            "path": request.url.path,
            "client_ip": request.client.host
        }
        log_metric(error_metric)
        raise e

    process_time = (time.time() - start_time) * 1000  # milliseconds
    metric = {
        "type": "request",
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": round(process_time, 2),
        "client_ip": request.client.host,
    }
    log_metric(metric)
    return response

# ➡️ APM Event Tracker
@app.post("/apm/track_event/")
async def track_event(event: dict):
    event["type"] = "custom_event"
    event["timestamp"] = datetime.utcnow().isoformat()
    log_metric(event)
    return {"status": "success", "message": "Event tracked"}

# ➡️ Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "UP", "time": datetime.utcnow().isoformat()}

# ➡️ Contact form submission (with redirect)
@app.post("/contact")
async def contact_form(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    submission = {
        "timestamp": datetime.utcnow().isoformat(),
        "name": name,
        "email": email,
        "message": message
    }
    with open(contact_file, "a") as f:
        f.write(json.dumps(submission) + "\n")

    # ✅ Redirect back to website contact page after successful submit
    return RedirectResponse(url="http://52.170.6.111/contact.html", status_code=303)
