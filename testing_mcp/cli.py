import typer

from testing_mcp.server.app import run_server

app = typer.Typer(
    name="testing-mcp",
    help="Universal AI-powered testing server built on the Model Context Protocol",
)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind to"),
) -> None:
    """Start the MCP testing server in SSE mode."""
    run_server(host=host, port=port)


@app.command()
def stdio() -> None:
    """Start the MCP testing server in stdio mode (for Claude Desktop, etc.)."""
    from testing_mcp.server.stdio import run_stdio
    run_stdio()


@app.command()
def version() -> None:
    """Show the version."""
    import importlib.metadata

    try:
        ver = importlib.metadata.version("testing-mcp")
    except importlib.metadata.PackageNotFoundError:
        ver = "0.1.0 (dev)"
    typer.echo(f"Testing MCP v{ver}")


if __name__ == "__main__":
    app()
