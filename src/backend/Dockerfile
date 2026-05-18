# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

RUN groupadd -r mchat && useradd -r -g mchat mchat -d /app

WORKDIR /app

COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY .env.example ./

ENV PATH=/root/.local/bin:$PATH

RUN mkdir -p uploads skills && chown -R mchat:mchat /app

USER mchat

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3001/api/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
