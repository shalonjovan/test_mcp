# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY testing_mcp/ testing_mcp/

RUN pip install --no-cache-dir build hatchling \
    && python -m build --wheel

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid 1001 --home-dir /app app

WORKDIR /app

# Install minimal runtime deps (no build tools)
RUN pip install --no-cache-dir pipx && \
    pipx ensurepath && \
    pipx install playwright

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl && \
    python -m playwright install chromium

EXPOSE 8080

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/live')" || exit 1

ENTRYPOINT ["testing-mcp"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
