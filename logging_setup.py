"""
Задача 28: structlog — JSON логи в терминал И в файл bot.log
"""
import logging
import logging.handlers
import sys
import uuid
 
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
 
 
def setup_tracing(service_name: str = "mcp-telegram-bot") -> trace.Tracer:
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        import socket
        socket.setdefaulttimeout(2)
        socket.getaddrinfo("jaeger", 6831)
        jaeger_exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        print("✅ Jaeger трассировка подключена")
    except Exception:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        print("⚠️  Jaeger недоступен — трейсы в консоль")
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)
 
 
def setup_logging(log_file: str = "bot.log") -> None:
    """
    JSON логи идут:
    1. В терминал (stdout)
    2. В файл bot.log (с ротацией — макс 5 МБ, 3 файла)
    """
    # Хендлер для терминала
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
 
    # Хендлер для файла с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
 
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[console_handler, file_handler],
    )
 
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
 
 
def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
 
 
def new_request_id() -> str:
    return str(uuid.uuid4())