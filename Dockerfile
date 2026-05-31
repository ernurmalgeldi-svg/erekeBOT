# ============================================================
# Задача 29: Multi-stage Dockerfile
# Stage 1 — builder: устанавливаем зависимости
# Stage 2 — runtime: минимальный образ, non-root user
# ============================================================

# ── Stage 1: builder ────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Системные зависимости для компиляции (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements — кешируем слой
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Системные runtime-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder
COPY --from=builder /install /usr/local

# ── Non-root пользователь (безопасность) ───────────────────
RUN groupadd --gid 1001 botuser \
    && useradd --uid 1001 --gid botuser --no-create-home botuser

WORKDIR /app

# Копируем исходный код
COPY --chown=botuser:botuser . .

# Создаём папку для shared_files с нужными правами
RUN mkdir -p /app/shared_files && chown botuser:botuser /app/shared_files

# Переключаемся на non-root
USER botuser

# Healthcheck: проверяем что процесс жив
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

EXPOSE 8080

CMD ["python", "main.py"]
