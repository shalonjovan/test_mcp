FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pipx && \
    pipx ensurepath && \
    pipx install playwright

COPY pyproject.toml README.md ./
COPY testing_mcp/ testing_mcp/

RUN pip install --no-cache-dir -e ".[dev]" && \
    python -m playwright install chromium

EXPOSE 8080

ENTRYPOINT ["testing-mcp"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
