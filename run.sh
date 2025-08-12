#!/bin/bash

# run.sh - Glances MCP Server Process Manager
# Handles starting, stopping, and managing the MCP server with proper logging and PID management

set -euo pipefail

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration with environment variable defaults
GLANCES_MCP_LOG_DIR="${GLANCES_MCP_LOG_DIR:-logs}"
GLANCES_MCP_PID_DIR="${GLANCES_MCP_PID_DIR:-logs}"
GLANCES_MCP_HOST="${GLANCES_MCP_HOST:-0.0.0.0}"
GLANCES_MCP_PORT="${GLANCES_MCP_PORT:-8080}"
GLANCES_MCP_CONFIG_FILE="${GLANCES_MCP_CONFIG_FILE:-glances_mcp/config/config.json}"

# File paths
PID_FILE="${GLANCES_MCP_PID_DIR}/glances-mcp.pid"
LOG_FILE="${GLANCES_MCP_LOG_DIR}/glances-mcp.log"
ERROR_LOG_FILE="${GLANCES_MCP_LOG_DIR}/glances-mcp.error.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create necessary directories
create_dirs() {
    mkdir -p "$GLANCES_MCP_LOG_DIR"
    mkdir -p "$GLANCES_MCP_PID_DIR"
}

# Check if server is running
is_server_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            # Double check it's actually our process
            if ps -p "$pid" -o cmd= | grep -q "glances_mcp.main"; then
                echo "$pid"
                return 0
            else
                # PID file exists but process is not our server
                rm -f "$PID_FILE"
                return 1
            fi
        else
            # PID file exists but process is dead
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Stop existing server
stop_server() {
    local pid
    if pid=$(is_server_running); then
        log_info "Stopping existing server (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warn "Force killing server (PID: $pid)..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        log_info "Server stopped successfully"
    fi
}

# Start the server
start_server() {
    log_info "Starting Glances MCP Server..."
    log_info "Host: $GLANCES_MCP_HOST"
    log_info "Port: $GLANCES_MCP_PORT"
    log_info "Config: $GLANCES_MCP_CONFIG_FILE"
    log_info "Logs: $LOG_FILE"
    log_info "PID: $PID_FILE"
    
    # Start server in background
    nohup python -m glances_mcp.main \
        --config "$GLANCES_MCP_CONFIG_FILE" \
        --host "$GLANCES_MCP_HOST" \
        --port "$GLANCES_MCP_PORT" \
        > "$LOG_FILE" 2> "$ERROR_LOG_FILE" &
    
    local server_pid=$!
    echo "$server_pid" > "$PID_FILE"
    
    # Give server a moment to start
    sleep 2
    
    # Verify server started successfully
    if ! ps -p "$server_pid" > /dev/null 2>&1; then
        log_error "Failed to start server"
        rm -f "$PID_FILE"
        log_error "Error log:"
        cat "$ERROR_LOG_FILE" 2>/dev/null || echo "No error log available"
        exit 1
    fi
    
    log_info "Server started successfully (PID: $server_pid)"
    log_info "Press Ctrl+C to stop following logs (server will continue running)"
}

# Follow logs with trap for graceful exit
follow_logs() {
    # Set up trap to handle Ctrl+C - only exit log following, not server
    trap 'log_info "\nStopping log follow (server continues running)"; exit 0' INT
    
    # Follow the logs
    tail -f "$LOG_FILE" 2>/dev/null &
    local tail_pid=$!
    
    # Also follow error logs if they have content
    if [ -s "$ERROR_LOG_FILE" ]; then
        log_warn "Error log has content:"
        tail -f "$ERROR_LOG_FILE" 2>/dev/null &
        local error_tail_pid=$!
    fi
    
    # Wait for tail processes
    wait $tail_pid 2>/dev/null || true
    [ ! -z "${error_tail_pid:-}" ] && kill $error_tail_pid 2>/dev/null || true
}

# Show server status
show_status() {
    local pid
    if pid=$(is_server_running); then
        log_info "Server is running (PID: $pid)"
        log_info "Logs: $LOG_FILE"
        log_info "Errors: $ERROR_LOG_FILE"
        return 0
    else
        log_warn "Server is not running"
        return 1
    fi
}

# Show usage
show_help() {
    echo "Usage: $0 [start|stop|restart|status|logs|help]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the server (default if no command given)"
    echo "  stop     - Stop the server"
    echo "  restart  - Stop and start the server"
    echo "  status   - Show server status"
    echo "  logs     - Follow server logs"
    echo "  help     - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GLANCES_MCP_LOG_DIR     - Log directory (default: logs)"
    echo "  GLANCES_MCP_PID_DIR     - PID file directory (default: logs)"
    echo "  GLANCES_MCP_HOST        - Server host (default: 0.0.0.0)"
    echo "  GLANCES_MCP_PORT        - Server port (default: 8080)"
    echo "  GLANCES_MCP_CONFIG_FILE - Config file path (default: glances_mcp/config/config.json)"
}

# Main execution
main() {
    local command="${1:-start}"
    
    create_dirs
    
    case "$command" in
        "start")
            stop_server
            start_server
            follow_logs
            ;;
        "stop")
            stop_server
            ;;
        "restart")
            stop_server
            start_server
            log_info "Server restarted. Use '$0 logs' to follow logs."
            ;;
        "status")
            show_status
            ;;
        "logs")
            if show_status > /dev/null; then
                follow_logs
            else
                log_error "Server is not running"
                exit 1
            fi
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"