import os

from opentelemetry import trace

from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.trace import TracerProvider

from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter
)

from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor
)


SERVICE_NAME = "flashcache-api"


def configure_tracing(app):

    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "service.version": "1.0.0"
        }
    )

    provider = TracerProvider(
        resource=resource
    )

    tracing_enabled = os.getenv(
        "FLASHCACHE_TRACING",
        "true"
    ).lower() == "true"

    if tracing_enabled:

        exporter = ConsoleSpanExporter()

        processor = BatchSpanProcessor(
            exporter
        )

        provider.add_span_processor(
            processor
        )

    trace.set_tracer_provider(
        provider
    )

    FastAPIInstrumentor.instrument_app(
        app
    )


tracer = trace.get_tracer(
    SERVICE_NAME
)