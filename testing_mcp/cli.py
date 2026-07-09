import importlib.metadata
from pathlib import Path

import typer

from testing_mcp.log import get_logger, setup_logging
from testing_mcp.server.app import run_server
from testing_mcp.utils.config import load_settings

log = get_logger(__name__)

app = typer.Typer(
    name="testing-mcp",
    help="Universal AI-powered testing server built on the Model Context Protocol",
)


def _get_version() -> str:
    try:
        return importlib.metadata.version("testing-mcp")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0 (dev)"


@app.command()
def serve(
    host: str = typer.Option(
        None, "--host", "-H", help="Host to bind to (default from config/env)"
    ),
    port: int = typer.Option(
        None, "--port", "-p", help="Port to bind to (default from config/env)"
    ),
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """Start the MCP testing server in SSE mode."""
    settings = load_settings(config)
    setup_logging(settings.log_level)
    log.info("testing-mcp v%s starting", settings.version)
    run_server(
        host=host or settings.host,
        port=port or settings.port,
    )


@app.command()
def stdio() -> None:
    """Start the MCP testing server in stdio mode (for Claude Desktop, etc.)."""
    from testing_mcp.server.stdio import run_stdio

    settings = load_settings()
    setup_logging(settings.log_level)
    run_stdio()


@app.command()
def version() -> None:
    """Show the version."""
    typer.echo(f"Testing MCP v{_get_version()}")


if __name__ == "__main__":
    app()
