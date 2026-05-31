"""
Задача 28: Структурированное логирование через structlog + OpenTelemetry + Jaeger
"""
import logging
import sys
import uuid
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource

# ── OpenTelemetry: настройка провайдера и экспорта в Jaeger ──────────────────

def setup_tracing(service_name: str = "mcp-telegram-bot"):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",   # имя сервиса в docker-compose
        agent_port=6831,
    )
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


tracer = None  # инициализируется в main()


# ── structlog: JSON-логи с request_id ────────────────────────────────────────

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,          # request_id из контекста
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),              # JSON вывод
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Перенаправляем стандартный logging → structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str = __name__):
    return structlog.get_logger(name)


def new_request_id() -> str:
    return str(uuid.uuid4())
