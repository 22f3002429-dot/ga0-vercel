import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

try:
    with DATA_PATH.open() as f:
        DATA = json.load(f)
except Exception as exc:
    raise RuntimeError(f"Could not load telemetry file: {DATA_PATH}") from exc


@app.post("/")
def metrics(payload: dict):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)

    result = {}

    for region in regions:
        records = [row for row in DATA if row.get("region") == region]

        if not records:
            raise HTTPException(status_code=404, detail=f"No data for region: {region}")

        latencies = [row["latency_ms"] for row in records]
        uptimes = [row["uptime"] for row in records]

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": sum(value > threshold for value in latencies),
        }

    return result
