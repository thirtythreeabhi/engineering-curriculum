"""Application Insights and OpenTelemetry distributed tracing."""

import time
import uuid
from typing import Any, Dict, List, Optional


class AppInsightsTelemetry:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or "InstrumentationKey=00000000-0000-0000-0000-000000000000"
        self.recorded_spans: List[Dict[str, Any]] = []
        self.recorded_metrics: List[Dict[str, Any]] = []

    def start_span(self, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        return {
            "name": name,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_id": parent_id,
            "start_time": time.perf_counter(),
            "attributes": {},
        }

    def end_span(self, span: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
        duration_ms = (time.perf_counter() - span["start_time"]) * 1000.0
        record = {
            **span,
            "duration_ms": round(duration_ms, 2),
            "status_code": status_code,
            "timestamp": time.time(),
        }
        self.recorded_spans.append(record)
        return record

    def track_metric(self, name: str, value: float, properties: Optional[Dict[str, str]] = None) -> None:
        self.recorded_metrics.append({
            "name": name,
            "value": value,
            "properties": properties or {},
            "timestamp": time.time(),
        })
