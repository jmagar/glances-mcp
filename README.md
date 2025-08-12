# Glances MCP Server

A comprehensive Model Context Protocol (MCP) server for infrastructure monitoring using Glances. This server enables AI assistants to monitor, analyze, and provide intelligent insights about your infrastructure through a rich set of tools, prompts, and resources.

## Features

### Core Monitoring Tools
- **Server Discovery & Status**: List and health check Glances servers
- **System Metrics**: CPU, memory, load, uptime monitoring
- **Storage Monitoring**: Disk usage and I/O statistics
- **Network Analysis**: Interface statistics and connection monitoring
- **Process Management**: Top processes and detailed process information
- **Container Support**: Docker/Podman container monitoring

### Advanced Analytics
- **Health Scoring**: Composite health scores with component breakdown
- **Performance Comparison**: Historical baseline comparison
- **Anomaly Detection**: Statistical anomaly detection in metrics
- **Capacity Analysis**: Resource utilization and growth projections

### Alert Management
- **Real-time Alerting**: Configurable alert rules and thresholds
- **Alert History**: Historical alert tracking and pattern analysis
- **Alert Patterns**: Recurring issue identification and correlation

### Capacity Planning
- **Resource Prediction**: ML-based resource need forecasting
- **Server Comparison**: Cross-server performance and efficiency analysis
- **Growth Modeling**: Trend-based capacity planning with scenarios

### AI-Powered Analysis
- **System Health Analysis**: Comprehensive infrastructure assessment
- **Performance Troubleshooting**: Systematic issue investigation
- **Capacity Planning Reports**: Strategic capacity planning analysis
- **Incident Response**: Dynamic troubleshooting procedures
- **Security Assessment**: Infrastructure security evaluation

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and start the services**:
```bash
git clone <repository>
cd glances-mcp
docker-compose up -d
```

2. **The server will start with**:
   - Glances MCP Server on port 8080
   - Two demo Glances servers (ports 61208, 61209)
   - Automatic service discovery and monitoring

3. **Access the demo Glances web interfaces**:
   - Demo Server 1: http://localhost:61208 (user: `glances`, pass: `demo123`)
   - Demo Server 2: http://localhost:61209 (user: `glances`, pass: `demo123`)

### Development Setup

1. **Install UV package manager**:
```bash
pip install uv
```

2. **Create and activate virtual environment**:
```bash
uv venv --python 3.11
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
```

3. **Install dependencies**:
```bash
uv pip install -e ".[dev]"
```

4. **Run the server**:
```bash
python -m glances_mcp.main --config glances_mcp/config/config.json --debug
```

## Configuration

### Server Configuration

Create a `glances_mcp/config/config.json` file with your Glances servers:

```json
{
  "servers": [
    {
      "alias": "production-web-01",
      "host": "10.0.1.10",
      "port": 61208,
      "protocol": "https",
      "username": "glances",
      "password": "secure_password",
      "environment": "production",
      "region": "us-east-1",
      "tags": ["web", "frontend", "critical"],
      "timeout": 30,
      "enabled": true
    }
  ],
  "alert_rules": [
    {
      "name": "high_cpu_usage",
      "metric_path": "cpu.total",
      "thresholds": {
        "warning": 80.0,
        "critical": 90.0,
        "unit": "%",
        "comparison": "gt"
      },
      "enabled": true,
      "cooldown_minutes": 15
    }
  ]
}
```

### Environment Variables

Configure the server using environment variables:

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

## Usage with Claude Desktop

### MCP Configuration

Add to your Claude Desktop MCP configuration:

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

### Example Queries

**System Health Assessment**:
```
Please analyze the health of our infrastructure and provide recommendations.
```

**Performance Troubleshooting**:
```
Server web-01 is experiencing slow response times. Help me investigate the root cause.
```

**Capacity Planning**:
```
Generate a 6-month capacity plan for our production environment.
```

**Alert Analysis**:
```
What alert patterns have we seen this week and what do they indicate?
```

## MCP Tools

### Basic Monitoring
- `list_servers` - List all configured servers with status
- `get_server_status` - Detailed server health information
- `get_system_overview` - System metrics overview
- `get_detailed_metrics` - Extended system metrics
- `get_disk_usage` - Disk space and usage information
- `get_network_stats` - Network interface statistics
- `get_top_processes` - Top processes by resource usage
- `get_containers` - Container monitoring and statistics

### Advanced Analytics
- `generate_health_score` - Comprehensive health scoring
- `performance_comparison` - Historical performance analysis
- `detect_anomalies` - Statistical anomaly detection
- `capacity_analysis` - Resource capacity assessment

### Alert Management
- `check_alert_conditions` - Evaluate alert conditions
- `get_alert_history` - Historical alert analysis
- `get_alert_summary` - Alert summary statistics
- `analyze_alert_patterns` - Pattern analysis and insights

### Capacity Planning
- `predict_resource_needs` - Resource growth forecasting
- `compare_servers` - Cross-server performance comparison

## MCP Prompts

### Analysis Prompts
- `system_health_analysis` - Comprehensive infrastructure assessment
- `performance_troubleshooting` - Systematic issue investigation
- `capacity_planning_report` - Strategic capacity planning

### Operational Prompts
- `incident_response_runbook` - Dynamic incident procedures
- `maintenance_planning` - Maintenance window planning
- `security_assessment` - Security posture evaluation

### Reporting Prompts
- `executive_dashboard` - High-level infrastructure overview
- `technical_deep_dive` - Detailed technical analysis

## MCP Resources

- `glances://config/servers` - Server inventory and configuration
- `glances://config/thresholds` - Alert thresholds and rules
- `glances://config/maintenance_windows` - Maintenance schedules
- `glances://config/settings` - Application configuration

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=glances_mcp --cov-report=html

# Run integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black glances_mcp/ tests/

# Lint code
ruff check glances_mcp/ tests/

# Type checking
mypy glances_mcp/
```

### Adding New Features

1. **Tools**: Add to `glances_mcp/tools/` directory
2. **Prompts**: Add to `glances_mcp/prompts/` directory  
3. **Resources**: Add to `glances_mcp/resources/` directory
4. **Services**: Add to `glances_mcp/services/` directory
5. **Register**: Update `glances_mcp/server.py` to register new components

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude AI     │    │  Other MCP      │    │   Web Clients   │
│   Assistant     │    │   Clients       │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    Glances MCP Server     │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │     FastMCP        │  │
                    │  │   (Tools, Prompts, │  │
                    │  │    Resources)      │  │
                    │  └─────────────────────┘  │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │   Services Layer   │  │
                    │  │                    │  │
                    │  │ • Alert Engine     │  │
                    │  │ • Baseline Manager │  │
                    │  │ • Health Calculator│  │
                    │  │ • Client Pool      │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────┴───────┐    ┌───────────┴──────────┐    ┌─────────┴────────┐
│   Glances     │    │     Glances          │    │    Glances       │
│   Server 1    │    │     Server 2         │    │    Server N      │
│               │    │                      │    │                  │
│ (Production)  │    │   (Staging)          │    │  (Development)   │
└───────────────┘    └──────────────────────┘    └──────────────────┘
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

## Changelog

### v1.0.0
- Initial release with comprehensive monitoring capabilities
- FastMCP 2.11.1 integration with streamable HTTP transport
- Advanced analytics and capacity planning tools
- AI-powered analysis prompts and resources
- Docker deployment support
- Comprehensive test suite