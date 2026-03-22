import os
import time
from typing import Optional

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, REGISTRY
from prometheus_client.openmetrics.exposition import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

OBSERVABILITY_ENABLED = os.getenv("ENABLE_OBSERVABILITY", "0") == "1"
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "uc-buscacursos-api")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


# Prometheus metrics
REQUEST_COUNTER = Counter(
    "fastapi_requests_total",
    "Total number of requests",
    labelnames=("method", "path", "status"),
)

REQUEST_LATENCY = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of request durations (seconds)",
    labelnames=("method", "path", "status"),
)


def _init_tracing() -> Optional[TracerProvider]:
    """
    Configure OpenTelemetry tracing with OTLP/Tempo exporter.
    Returns the tracer provider if observability is enabled, else None.
    """
    if not OBSERVABILITY_ENABLED:
        return None

    resource = Resource.create({"service.name": SERVICE_NAME})
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    LoggingInstrumentor().instrument(set_logging_format=True)
    return tracer_provider


def _add_metrics_route(app: FastAPI) -> None:
    """
    Expose /metrics in OpenMetrics format for Prometheus scraping.
    """

    @app.get("/metrics")
    async def metrics() -> Response:  # pragma: no cover - thin wrapper
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def _add_metrics_middleware(app: FastAPI) -> None:
    """
    Record request metrics with exemplars using the current trace ID.
    """

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        method = request.method
        path = request.url.path
        status = response.status_code

        REQUEST_COUNTER.labels(method, path, status).inc()

        # Attach exemplar with trace ID when available
        span = trace.get_current_span()
        span_ctx = span.get_span_context()
        trace_id = trace.format_trace_id(span_ctx.trace_id)
        exemplar = {"TraceID": trace_id} if span_ctx.is_valid else None

        if exemplar:
            REQUEST_LATENCY.labels(method, path, status).observe(duration, exemplar=exemplar)
        else:
            REQUEST_LATENCY.labels(method, path, status).observe(duration)

        return response


def setup_observability(app: FastAPI) -> None:
    """
    Enable optional observability (Tempo traces, Prometheus metrics, Loki-friendly logs).
    Controlled by ENABLE_OBSERVABILITY=1.
    """
    if not OBSERVABILITY_ENABLED:
        return

    tracer_provider = _init_tracing()
    if tracer_provider:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    _add_metrics_route(app)
    _add_metrics_middleware(app)
