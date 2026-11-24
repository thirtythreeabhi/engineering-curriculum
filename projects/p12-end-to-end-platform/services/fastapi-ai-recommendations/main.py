"""FastAPI AI Recommendation Microservice."""

import time
from typing import List
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="AI Recommendation Service", version="1.0.0")

# In-memory metrics
REQUEST_COUNT = 0


class ProductRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    relevance_score: float
    reason: str


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ai-recommendations"}


@app.get("/recommendations/{user_id}", response_model=List[ProductRecommendation])
def get_recommendations(user_id: int):
    global REQUEST_COUNT
    REQUEST_COUNT += 1

    # Simulated personalized collaborative filtering & embedding ranking
    return [
        ProductRecommendation(
            sku="KEYBOARD-MECH",
            name="Keychron Q1 Pro",
            category="Accessories",
            relevance_score=0.96,
            reason="High co-affinity with previously purchased ThinkPad Carbon X1",
        ),
        ProductRecommendation(
            sku="HEADSET-PRO",
            name="Sony WH-1000XM5",
            category="Audio",
            relevance_score=0.88,
            reason="Trending among engineering team profiles",
        ),
    ]


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return f"""# HELP ai_recommendations_served_total Total recommendation requests served
# TYPE ai_recommendations_served_total counter
ai_recommendations_served_total {REQUEST_COUNT}
# HELP ai_model_inference_latency_seconds Latency of recommendation scoring
# TYPE ai_model_inference_latency_seconds gauge
ai_model_inference_latency_seconds 0.012
"""
