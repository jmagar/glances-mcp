FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv --python 3.11 /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
RUN uv pip install --system --no-cache -e .

# Copy application code
COPY glances_mcp/ glances_mcp/

# Create data directory for baselines and state
RUN mkdir -p data/baselines

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import asyncio; from glances_mcp.server import get_server; asyncio.run(get_server())" || exit 1

# Expose port
EXPOSE 8080

# Set environment variables
ENV GLANCES_MCP_HOST=0.0.0.0
ENV GLANCES_MCP_PORT=8080
ENV GLANCES_MCP_LOG_LEVEL=INFO
ENV GLANCES_MCP_LOG_FORMAT=json

# Run the application
CMD ["python", "-m", "glances_mcp.main"]