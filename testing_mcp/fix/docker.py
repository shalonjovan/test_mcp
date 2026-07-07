from __future__ import annotations

from pathlib import Path
from typing import Any

from testing_mcp.analyzers.project import analyze_project


def generate_dockerfile(path: str = ".") -> dict[str, Any]:
    root = Path(path).resolve()
    analysis = analyze_project(root)
    languages = analysis.get("languages", {})

    lines: list[str] = []

    if "python" in languages:
        lines = [
            "FROM python:3.12-slim",
            "",
            "WORKDIR /app",
            "",
            "COPY pyproject.toml .",
            "RUN pip install --no-cache-dir -e .",
            "",
            "COPY . .",
            "",
            'CMD ["python", "-m", "app.main"]',
        ]
    elif "node" in languages or "javascript" in languages or "typescript" in languages:
        lines = [
            "FROM node:20-slim",
            "",
            "WORKDIR /app",
            "",
            "COPY package*.json .",
            "RUN npm ci --only=production",
            "",
            "COPY . .",
            "",
            "EXPOSE 3000",
            'CMD ["node", "dist/index.js"]',
        ]
    elif "go" in languages:
        lines = [
            "FROM golang:1.22 AS builder",
            "",
            "WORKDIR /app",
            "COPY go.mod go.sum ./",
            "RUN go mod download",
            "COPY . .",
            "RUN CGO_ENABLED=0 go build -o /app/server .",
            "",
            "FROM alpine:3.19",
            "COPY --from=builder /app/server /app/server",
            'CMD ["/app/server"]',
        ]
    elif "rust" in languages:
        lines = [
            "FROM rust:1.77 AS builder",
            "",
            "WORKDIR /app",
            "COPY . .",
            "RUN cargo build --release",
            "",
            "FROM debian:bookworm-slim",
            "COPY --from=builder /app/target/release/app /app/app",
            'CMD ["/app/app"]',
        ]
    elif "java" in languages:
        lines = [
            "FROM eclipse-temurin:21-jdk AS builder",
            "",
            "WORKDIR /app",
            "COPY . .",
            "RUN ./mvnw package -DskipTests",
            "",
            "FROM eclipse-temurin:21-jre",
            "COPY --from=builder /app/target/*.jar app.jar",
            'CMD ["java", "-jar", "app.jar"]',
        ]
    else:
        lines = [
            "FROM python:3.12-slim",
            "",
            "WORKDIR /app",
            "",
            "COPY . .",
            "",
            'CMD ["python", "main.py"]',
        ]

    lines.insert(2, f"LABEL description=\"{root.name}\"")

    dockerfile_path = root / "Dockerfile"
    content = "\n".join(lines) + "\n"
    dockerfile_path.write_text(content)

    return {
        "path": str(dockerfile_path),
        "language": list(languages.keys())[0] if languages else "unknown",
        "lines": len(lines),
        "content": content,
    }
