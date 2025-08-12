# Glances MCP Server - Claude Code Documentation

A comprehensive Model Context Protocol (MCP) server for infrastructure monitoring using Glances. This server enables AI assistants to monitor, analyze, and provide intelligent insights about your infrastructure through a rich set of tools, prompts, and resources.

## Project Structure

```
glances-mcp/
├── glances_mcp/              # Main application package
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── server.py            # FastMCP server configuration
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   ├── config.json      # Default configuration
│   │   ├── models.py        # Pydantic models for config
│   │   ├── settings.py      # Settings management
│   │   └── validation.py    # Configuration validation
│   ├── tools/               # MCP tools implementation
│   │   ├── __init__.py
│   │   ├── basic_monitoring.py    # Core monitoring tools
│   │   ├── advanced_analytics.py  # Analytics and health scoring
│   │   ├── alert_management.py    # Alert tools
│   │   └── capacity_planning.py   # Capacity planning tools
│   ├── prompts/             # MCP prompts for AI analysis
│   │   ├── __init__.py
│   │   ├── analysis.py      # System analysis prompts
│   │   ├── reporting.py     # Reporting prompts
│   │   └── troubleshooting.py  # Troubleshooting prompts
│   ├── resources/           # MCP resources for configuration
│   │   ├── __init__.py
│   │   ├── configuration.py # Configuration resources
│   │   ├── historical.py    # Historical data resources
│   │   └── knowledge.py     # Knowledge base resources
│   ├── services/            # Core business logic
│   │   ├── __init__.py
│   │   ├── glances_client.py     # Glances API client
│   │   ├── alert_engine.py       # Alert processing
│   │   ├── baseline_manager.py   # Performance baselines
│   │   └── health_calculator.py  # Health scoring
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── helpers.py       # Helper functions
│       ├── logging.py       # Logging configuration
│       └── metrics.py       # Metrics utilities
├── docs/                    # Documentation
├── tests/                   # Test suite
├── pyproject.toml          # Python project configuration
├── uv.lock                 # UV lock file
├── run.sh                  # Process management script
├── docker-compose.yml      # Docker composition
├── Dockerfile              # Docker image definition
└── README.md               # Project documentation
```

## Development Workflow

### Prerequisites

- Python 3.11+
- UV package manager
- Docker (for containerized development)

### Setup

1. **Install UV package manager**:
   ```bash
   pip install uv
   ```

2. **Create and activate virtual environment**:
   ```bash
   uv venv --python 3.11
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -e ".[dev]"
   ```

### Running the Server

#### Development Mode
```bash
python -m glances_mcp.main --config glances_mcp/config/config.json --debug
```

#### Production Mode
```bash
./run.sh
```

#### Docker Compose
```bash
docker-compose up -d
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=glances_mcp --cov-report=html

# Run integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black glances_mcp/ tests/

# Lint code
ruff check glances_mcp/ tests/ --fix

# Type checking
mypy glances_mcp/
```

## Architecture Overview

### MCP Components

1. **Tools** (`glances_mcp/tools/`): Direct function calls for monitoring operations
2. **Prompts** (`glances_mcp/prompts/`): AI-powered analysis and reporting
3. **Resources** (`glances_mcp/resources/`): Configuration and knowledge base access

### Service Layer

1. **GlancesClient** (`services/glances_client.py`): HTTP client for Glances servers
2. **AlertEngine** (`services/alert_engine.py`): Alert rule evaluation and management
3. **BaselineManager** (`services/baseline_manager.py`): Performance baseline tracking
4. **HealthCalculator** (`services/health_calculator.py`): Composite health scoring

### Configuration

Configuration is managed through Pydantic models with environment variable support:

- **ServerConfig**: Glances server definitions
- **AlertRule**: Alert rule definitions
- **Settings**: Application-wide settings

## Key Features

### Monitoring Tools
- Server discovery and health checking
- Real-time system metrics (CPU, memory, disk, network)
- Process monitoring and analysis
- Container monitoring support
- Cross-server performance comparison

### Advanced Analytics
- Composite health scoring
- Performance baseline comparison
- Statistical anomaly detection
- Capacity utilization analysis
- Growth trend modeling

### Alert Management
- Configurable alert rules and thresholds
- Real-time alert evaluation
- Alert history and pattern analysis
- Automated alert correlation

### AI-Powered Analysis
- System health assessment prompts
- Performance troubleshooting guides
- Capacity planning reports
- Incident response procedures
- Security assessment frameworks

## Integration with Claude Desktop

### MCP Configuration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "glances": {
      "command": "python",
      "args": ["-m", "glances_mcp.main"],
      "cwd": "/path/to/glances-mcp",
      "env": {
        "GLANCES_MCP_CONFIG_FILE": "glances_mcp/config/config.json"
      }
    }
  }
}
```

### Example Interactions

- **Health Assessment**: "Analyze the current health of our infrastructure"
- **Performance Troubleshooting**: "Server web-01 is slow, help investigate"
- **Capacity Planning**: "Generate a 6-month capacity plan"
- **Alert Analysis**: "What alert patterns indicate system issues?"

## Development Guidelines

### Adding New Features

1. **Tools**: Implement in `glances_mcp/tools/` and register in `server.py`
2. **Prompts**: Add to `glances_mcp/prompts/` for AI-powered analysis
3. **Resources**: Create in `glances_mcp/resources/` for configuration access
4. **Services**: Add business logic to `glances_mcp/services/`

### Code Standards

- Use type hints throughout (enforced by mypy)
- Follow PEP 8 style (enforced by black and ruff)
- Write comprehensive tests for new functionality
- Document public APIs with docstrings
- Use structured logging with contextual information

### Configuration Management

- All configuration through Pydantic models
- Environment variable override support
- Validation at startup with clear error messages
- Hot-reload support for development

## Deployment

### Docker Deployment

The project includes a multi-stage Dockerfile optimized for production:

- Uses Python 3.11 slim base image
- UV package manager for fast dependency installation
- Non-root user for security
- Health checks included
- Optimized layer caching

### Environment Variables

Configure the server through environment variables:

```bash
# Server Configuration
GLANCES_MCP_HOST=0.0.0.0
GLANCES_MCP_PORT=8080
GLANCES_MCP_DEBUG=false

# Logging
GLANCES_MCP_LOG_LEVEL=INFO
GLANCES_MCP_LOG_FORMAT=json

# Performance
GLANCES_MCP_MAX_CONCURRENT_REQUESTS=100
GLANCES_MCP_GLANCES_TIMEOUT=30

# Data Retention
GLANCES_MCP_BASELINE_RETENTION_DAYS=7
GLANCES_MCP_ALERT_HISTORY_RETENTION_DAYS=30
```

### Security Considerations

- Use strong authentication for Glances servers
- Implement proper SSL/TLS for production deployments
- Regular security updates for dependencies
- Network isolation through Docker networks
- Principle of least privilege for container execution

## Troubleshooting

### Common Issues

1. **Glances Server Connection**: Check network connectivity and credentials
2. **Memory Usage**: Monitor baseline data retention settings
3. **Performance**: Adjust concurrent request limits and timeouts
4. **Alerts**: Verify alert rule syntax and thresholds

### Debugging

Enable debug mode for detailed logging:

```bash
python -m glances_mcp.main --debug
```

### Log Analysis

Logs are structured JSON for easy parsing:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "glances_mcp.services.glances_client",
  "message": "Successfully connected to server",
  "server_alias": "web-01",
  "response_time": 0.123
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all quality checks pass
5. Submit a pull request

The project uses modern Python tooling for a smooth development experience:
- UV for fast dependency management
- Black for consistent code formatting
- Ruff for comprehensive linting
- MyPy for static type checking
- Pytest for testing with asyncio support

## License

MIT License - see LICENSE file for details.