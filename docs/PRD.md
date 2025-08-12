[200~# Glances MCP Server - Product Requirements Document

**Version:** 1.0  
**Date:** August 6, 2025  
**Status:** Draft  

## Executive Summary

The Glances MCP Server is a Model Context Protocol server that enables AI assistants to monitor and analyze infrastructure through Glances monitoring data. Built with FastMCP Python and using streamable HTTP transport, it provides comprehensive system monitoring capabilities, intelligent alerting, and AI-powered infrastructure insights.

## Product Overview

### Vision
Enable AI assistants to become intelligent infrastructure monitoring partners, capable of real-time analysis, proactive alerting, and expert-level troubleshooting guidance across distributed Glances deployments.

### Goals
1. **Unified Monitoring Interface**: Single MCP endpoint for monitoring multiple Glances servers
2. **AI-Native Infrastructure Management**: Purpose-built for AI assistant integration
3. **Proactive Intelligence**: Move beyond reactive monitoring to predictive insights
4. **Expert Knowledge Access**: Embed SRE expertise through structured prompts and resources

### Success Metrics
- **Coverage**: Monitor 100% of infrastructure through single MCP endpoint
- **Response Time**: < 2 seconds for most monitoring queries
- **Alert Accuracy**: > 95% alert precision with < 5% false positives
- **AI Integration**: Seamless integration with Claude Desktop and other MCP clients

## Technical Specifications

### Core Technology Stack
- **Language**: Python 3.11+
- **MCP Framework**: FastMCP 2.11.1
- **Package Manager**: UV for dependency management
- **Transport**: Streamable HTTP (MCP 2025-03-26 specification)
- **HTTP Client**: aiohttp for async Glances API communication
- **Data Validation**: Pydantic for configuration and data models

### Architecture Requirements

#### Transport Layer
- **Protocol**: Streamable HTTP with single `/mcp` endpoint
- **Session Management**: Support for stateful sessions with unique session IDs
- **Resumability**: Support for connection resumption after drops
- **CORS**: Configurable CORS for web-based MCP clients

#### Configuration Management
```python
# Configuration schema using Pydantic
class GlancesServer(BaseModel):
    alias: str
    host: str
    port: int = 61208
    protocol: Literal["http", "https"] = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    environment: Optional[Literal["production", "staging", "development"]] = None
    region: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    timeout: int = 30

class AlertThreshold(BaseModel):
    metric: str
    warning: float
    critical: float
    unit: str

class MCPServerConfig(BaseModel):
    servers: List[GlancesServer]
    alert_thresholds: List[AlertThreshold]
    maintenance_windows: Optional[List[MaintenanceWindow]] = None
    performance_baseline_retention: int = 7  # days
    alert_history_retention: int = 30  # days
```

#### Package Management with UV
```toml
# pyproject.toml
[project]
name = "glances-mcp-server"
version = "1.0.0"
description = "MCP Server for Glances infrastructure monitoring"
requires-python = ">=3.11"
dependencies = [
    "fastmcp==2.11.1",
    "aiohttp>=3.9.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "asyncio-mqtt>=0.13.0",  # for future MQTT integration
    "structlog>=23.2.0",     # structured logging
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0", 
    "pytest-mock>=3.12.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
```

## Functional Requirements

### 1. Core Monitoring Tools

#### 1.1 Server Discovery & Status
- **Tool**: `list_servers`
  - List all configured Glances servers with metadata
  - Include environment, region, tags, and status
  - Return server capabilities and version info

- **Tool**: `get_server_status`
  - Health check for individual servers or all servers
  - Connection status, response time, API version
  - Last successful communication timestamp

#### 1.2 System Metrics Collection
- **Tool**: `get_system_overview`
  - CPU utilization (total and per-core)
  - Memory usage (used, available, cached, buffers)
  - System load averages (1min, 5min, 15min)
  - Uptime and system information

- **Tool**: `get_detailed_metrics`
  - Extended CPU metrics (user, system, iowait, steal)
  - Detailed memory breakdown (active, inactive, swap)
  - I/O statistics (read/write operations and bandwidth)
  - Context switches and interrupts

#### 1.3 Storage Monitoring
- **Tool**: `get_disk_usage`
  - Filesystem usage for all mount points
  - Disk space utilization percentages
  - Available space in human-readable format
  - I/O performance metrics

- **Tool**: `get_disk_io_stats`
  - Read/write IOPS per disk
  - Throughput (MB/s) per disk
  - I/O wait times and queue depths

#### 1.4 Network Monitoring
- **Tool**: `get_network_stats`
  - Interface-level traffic statistics
  - Bandwidth utilization (in/out)
  - Packet counts and error rates
  - Connection state summaries

- **Tool**: `get_network_connections`
  - Active connections by protocol
  - Listening ports and services
  - Connection state analysis

#### 1.5 Container Monitoring
- **Tool**: `get_containers`
  - Docker/Podman container statistics
  - Resource usage per container (CPU, memory, I/O)
  - Container health and status
  - Image information and uptime

- **Tool**: `get_container_details`
  - Detailed container inspection
  - Port mappings and volume mounts
  - Environment variables (filtered for security)

#### 1.6 Process Monitoring
- **Tool**: `get_top_processes`
  - Top processes by CPU or memory usage
  - Process tree and parent-child relationships
  - Resource consumption trends
  - Command line arguments (truncated for security)

- **Tool**: `get_process_details`
  - Detailed process information
  - Open files and network connections
  - Process status and scheduling information

### 2. Advanced Analytics Tools

#### 2.1 Alert Management
- **Tool**: `check_alert_conditions`
  - Evaluate current metrics against thresholds
  - Generate alerts with severity levels
  - Support for custom threshold configurations
  - Alert correlation and suppression logic

- **Tool**: `get_alert_history`
  - Historical alert data with filtering
  - Alert trends and patterns
  - Mean time to resolution tracking

#### 2.2 Performance Analysis
- **Tool**: `performance_comparison`
  - Compare current metrics against baselines
  - Detect performance regressions
  - Statistical analysis of metric trends
  - Performance scoring algorithms

- **Tool**: `generate_health_score`
  - Composite health scoring across metrics
  - Weighted scoring based on criticality
  - Health trend analysis
  - Risk assessment scoring

#### 2.3 Capacity Planning
- **Tool**: `capacity_analysis`
  - Current resource utilization assessment
  - Growth trend analysis
  - Time-to-exhaustion calculations
  - Scaling recommendations

- **Tool**: `predict_resource_needs`
  - Machine learning-based capacity forecasting
  - Seasonal pattern recognition
  - Growth scenario modeling
  - Cost optimization analysis

#### 2.4 Anomaly Detection
- **Tool**: `detect_anomalies`
  - Statistical anomaly detection in metrics
  - Behavioral pattern analysis
  - Outlier identification
  - Change point detection

### 3. Infrastructure Intelligence

#### 3.1 Comparative Analysis
- **Tool**: `compare_servers`
  - Side-by-side server comparisons
  - Resource efficiency analysis
  - Performance benchmarking
  - Configuration drift detection

- **Tool**: `environment_analysis`
  - Cross-environment performance comparison
  - Environment-specific optimizations
  - Resource allocation analysis

#### 3.2 Dependency Mapping
- **Tool**: `analyze_dependencies`
  - Service dependency identification
  - Resource correlation analysis
  - Impact assessment for changes
  - Failure scenario modeling

## MCP Primitives Implementation

### 1. Prompts

#### 1.1 System Analysis Prompts
- **`system_health_analysis`**
  - Comprehensive infrastructure health assessment
  - Multi-server analysis with correlation
  - Actionable recommendations with priorities
  - Executive summary generation

- **`performance_troubleshooting`**
  - Systematic performance issue investigation
  - Root cause analysis methodology
  - Step-by-step troubleshooting procedures
  - Resolution tracking and documentation

- **`capacity_planning_report`**
  - Long-term capacity planning analysis
  - Growth projection modeling
  - Resource optimization recommendations
  - Cost-benefit analysis for upgrades

#### 1.2 Operational Prompts
- **`incident_response_runbook`**
  - Dynamic incident response procedures
  - Context-aware troubleshooting steps
  - Escalation criteria and procedures
  - Post-incident analysis templates

- **`maintenance_planning`**
  - Maintenance window planning
  - Risk assessment for changes
  - Rollback procedures
  - Impact minimization strategies

- **`security_assessment`**
  - Security posture evaluation
  - Vulnerability identification
  - Compliance checking
  - Hardening recommendations

#### 1.3 Reporting Prompts
- **`executive_dashboard`**
  - High-level infrastructure overview
  - KPI tracking and trending
  - Business impact analysis
  - Strategic recommendations

- **`technical_deep_dive`**
  - Detailed technical analysis
  - Performance optimization opportunities
  - Architecture improvement suggestions
  - Technology upgrade pathways

### 2. Resources

#### 2.1 Configuration Resources
- **URI**: `glances://config/servers`
  - Complete server inventory
  - Configuration metadata
  - Environment and tag information
  - Connection parameters (credentials redacted)

- **URI**: `glances://config/thresholds`
  - Alert threshold configurations
  - Threshold modification history
  - Custom threshold templates

#### 2.2 Historical Resources
- **URI**: `glances://history/performance`
  - Performance baseline data
  - Historical trend analysis
  - Seasonal pattern data
  - Performance regression history

- **URI**: `glances://history/alerts`
  - Alert history and patterns
  - Resolution time tracking
  - Alert correlation data
  - False positive analysis

#### 2.3 Knowledge Resources
- **URI**: `glances://knowledge/runbooks`
  - Operational runbooks
  - Best practices documentation
  - Troubleshooting procedures
  - Escalation guidelines

- **URI**: `glances://knowledge/baselines`
  - Performance baselines
  - Capacity planning data
  - Growth trend analysis
  - Optimization opportunities

#### 2.4 Live Resources
- **URI**: `glances://live/dashboard`
  - Real-time infrastructure dashboard
  - Live metric streaming
  - Alert status updates
  - System health summary

- **URI**: `glances://live/topology`
  - Infrastructure topology map
  - Service dependency graph
  - Network connectivity status
  - Resource relationship mapping

## Non-Functional Requirements

### Performance Requirements
- **Response Time**: < 2 seconds for 95% of tool executions
- **Throughput**: Support 100+ concurrent MCP connections
- **Resource Usage**: < 512MB RAM under normal load
- **Scalability**: Support monitoring 100+ Glances servers

### Reliability Requirements
- **Availability**: 99.9% uptime for MCP server
- **Error Handling**: Graceful degradation when Glances servers unavailable
- **Recovery**: Automatic reconnection to failed Glances servers
- **Data Consistency**: Consistent data across multiple tool calls

### Security Requirements
- **Authentication**: Secure credential storage for Glances servers
- **Authorization**: Role-based access to sensitive operations
- **Encryption**: TLS support for production deployments
- **Audit Logging**: Complete audit trail of all operations

### Monitoring & Observability
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Metrics**: Prometheus-compatible metrics export
- **Health Checks**: Built-in health and readiness endpoints
- **Debugging**: Comprehensive debug logging capabilities

## Development Specifications

### Project Structure
```
glances-mcp-server/
├── pyproject.toml              # UV package configuration
├── uv.lock                     # UV lockfile
├── README.md                   # Project documentation
├── Dockerfile                  # Container build
├── docker-compose.yml          # Multi-container setup
├── .env.example               # Environment template
├── config/
│   ├── __init__.py
│   ├── models.py              # Pydantic models
│   ├── settings.py            # Configuration management
│   └── validation.py          # Input validation
├── src/
│   ├── __init__.py
│   ├── main.py                # Application entry point
│   ├── server.py              # MCP server implementation
│   ├── tools/                 # MCP tools
│   │   ├── __init__.py
│   │   ├── basic_monitoring.py
│   │   ├── advanced_analytics.py
│   │   ├── alert_management.py
│   │   └── capacity_planning.py
│   ├── prompts/               # MCP prompts
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── troubleshooting.py
│   │   └── reporting.py
│   ├── resources/             # MCP resources
│   │   ├── __init__.py
│   │   ├── configuration.py
│   │   ├── historical.py
│   │   └── knowledge.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── glances_client.py
│   │   ├── alert_engine.py
│   │   ├── baseline_manager.py
│   │   └── health_calculator.py
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── logging.py
│       ├── metrics.py
│       └── helpers.py
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tools.py
│   ├── test_prompts.py
│   ├── test_resources.py
│   └── integration/
│       ├── test_glances_integration.py
│       └── test_mcp_client.py
└── docs/                      # Documentation
    ├── api.md
    ├── deployment.md
    ├── configuration.md
    └── troubleshooting.md
```

### Development Environment Setup
```bash
# Create and activate UV environment
uv venv --python 3.11
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -e ".[dev]"

# Run in development mode
python -m src.main --config config/development.json

# Run tests
pytest tests/

# Type checking
mypy src/

# Code formatting
black src/ tests/
ruff check src/ tests/
```

### Configuration Management
```python
# config/settings.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    
    # Glances configuration
    glances_timeout: int = 30
    glances_retry_attempts: int = 3
    glances_retry_delay: int = 5
    
    # Performance configuration
    baseline_retention_days: int = 7
    alert_history_retention_days: int = 30
    max_concurrent_requests: int = 100
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "GLANCES_MCP_"
```

### Testing Strategy

#### Unit Tests
- **Tool Testing**: Mock Glances API responses for consistent testing
- **Prompt Testing**: Validate prompt structure and parameter handling
- **Resource Testing**: Test resource generation and formatting
- **Service Testing**: Test business logic with various scenarios

#### Integration Tests
- **Glances Integration**: Test against real Glances instances
- **MCP Client Testing**: Test with actual MCP clients
- **End-to-End Testing**: Complete workflow testing
- **Performance Testing**: Load testing with multiple clients

#### Test Data Management
```python
# tests/fixtures/
glances_responses/
├── cpu_response.json
├── memory_response.json
├── containers_response.json
└── error_responses.json
```

## Deployment Specifications

### Container Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install --system --no-cache -r uv.lock

# Copy application code
COPY src/ src/
COPY config/ config/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "-m", "src.main"]
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  glances-mcp:
    build: .
    container_name: glances-mcp-server
    ports:
      - "8080:8080"
    environment:
      - GLANCES_MCP_LOG_LEVEL=INFO
      - GLANCES_MCP_DEBUG=false
    volumes:
      - ./config/production.json:/app/config/config.json:ro
      - glances-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - monitoring

  # Example Glances server for testing
  glances-demo:
    image: nicolargo/glances:latest-full
    container_name: glances-demo
    ports:
      - "61208:61208"
    pid: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: -w -B 0.0.0.0 --username glances --password demo123
    networks:
      - monitoring

volumes:
  glances-data:

networks:
  monitoring:
    driver: bridge
```

### Environment Configuration
```bash
# .env.example
# Server Configuration
GLANCES_MCP_HOST=0.0.0.0
GLANCES_MCP_PORT=8080
GLANCES_MCP_DEBUG=false

# Logging Configuration  
GLANCES_MCP_LOG_LEVEL=INFO
GLANCES_MCP_LOG_FORMAT=json

# Performance Configuration
GLANCES_MCP_MAX_CONCURRENT_REQUESTS=100
GLANCES_MCP_GLANCES_TIMEOUT=30

# Data Retention
GLANCES_MCP_BASELINE_RETENTION_DAYS=7
GLANCES_MCP_ALERT_HISTORY_RETENTION_DAYS=30
```

## Quality Assurance

### Code Quality Standards
- **Type Hints**: 100% type coverage with mypy
- **Code Coverage**: Minimum 90% test coverage
- **Code Style**: Black formatting, Ruff linting
- **Documentation**: Comprehensive docstrings for all public APIs

### Performance Benchmarks
- **Tool Response Time**: < 2 seconds for 95% of operations
- **Memory Usage**: < 512MB under normal load
- **CPU Usage**: < 50% single core under normal load
- **Concurrent Connections**: Support 100+ simultaneous MCP clients

### Security Requirements
- **Dependency Scanning**: Regular security scans with safety/bandit
- **Credential Security**: No hardcoded credentials, secure storage
- **Input Validation**: Comprehensive input validation and sanitization
- **Error Handling**: No sensitive information in error messages

## Success Criteria

### Technical Success Metrics
1. **Functionality**: All tools, prompts, and resources working as specified
2. **Performance**: Meeting all response time and throughput requirements
3. **Reliability**: 99.9% uptime with graceful error handling
4. **Integration**: Seamless operation with Claude Desktop and other MCP clients

### User Experience Success Metrics
1. **Ease of Setup**: < 10 minutes from download to functional monitoring
2. **Query Success**: > 95% of user queries return actionable results
3. **Alert Accuracy**: < 5% false positive rate for alerts
4. **Documentation Quality**: Users can deploy without external support

### Business Success Metrics
1. **Adoption**: Integration with major MCP clients
2. **Community**: Active community contributions and feedback
3. **Extensibility**: Third-party extensions and integrations
4. **Maintenance**: Sustainable development and maintenance model

## Future Enhancements

### Phase 2 Features
- **Machine Learning**: Predictive analytics and anomaly detection
- **Multi-Cloud**: Support for cloud provider metrics integration
- **Advanced Alerting**: Smart alert correlation and suppression
- **Custom Dashboards**: User-configurable monitoring dashboards

### Phase 3 Features  
- **Automation**: Self-healing infrastructure capabilities
- **Integration**: ITSM and ticketing system integration
- **Compliance**: Automated compliance checking and reporting
- **AI Agents**: Autonomous infrastructure management agents

This PRD provides a comprehensive blueprint for building a production-ready Glances MCP server that transforms infrastructure monitoring into an AI-native experience.
