Here's how to set up Glances in containers for multi-device monitoring:

## Container Server Mode Setup

**Run Glances Server in Container:**
```bash
# Basic server mode
docker run -d --name glances-server \
  -p 61209:61209 \
  --pid host \
  --network host \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  nicolargo/glances:latest-full \
  -s -B 0.0.0.0

# With authentication
docker run -d --name glances-server \
  -p 61209:61209 \
  --pid host \
  --network host \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  nicolargo/glances:latest-full \
  -s -B 0.0.0.0 --username glances --password yourpassword
```

**Web Server Mode:**
```bash
docker run -d --name glances-web \
  -p 61208:61208 \
  --pid host \
  --network host \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  nicolargo/glances:latest-full \
  -w -B 0.0.0.0
```

## Multi-Server Browser Configuration

**Create Configuration File:**
```bash
# Create config directory
mkdir -p ~/glances-config

# Create glances.conf
cat > ~/glances-config/glances.conf << 'EOF'
[serverlist]
server_1_alias=Docker Host 1
server_1_name=192.168.1.10
server_1_port=61209
server_1_username=glances
server_1_password=yourpassword

server_2_alias=Docker Host 2  
server_2_name=192.168.1.11
server_2_port=61209
server_2_username=glances
server_2_password=yourpassword

server_3_alias=NAS Server
server_3_name=192.168.1.20
server_3_port=61209
server_3_username=glances
server_3_password=yourpassword

[elasticsearch]
host=192.168.1.5
port=9200
index=glances
EOF
```

**Run Central Browser:**
```bash
# TUI browser mode
docker run -it --rm \
  -v ~/glances-config/glances.conf:/glances/conf/glances.conf \
  nicolargo/glances:latest-full \
  --config /glances/conf/glances.conf --browser

# Web browser with server list
docker run -d --name glances-central \
  -p 61208:61208 \
  -v ~/glances-config/glances.conf:/glances/conf/glances.conf \
  nicolargo/glances:latest-full \
  --config /glances/conf/glances.conf -w --browser
```

## Docker Compose Setup

**Multi-Server docker-compose.yml:**
```yaml
version: '3.8'

services:
  # Central browser/dashboard
  glances-central:
    image: nicolargo/glances:latest-full
    container_name: glances-central
    ports:
      - "61208:61208"
    volumes:
      - ./glances.conf:/glances/conf/glances.conf
    command: --config /glances/conf/glances.conf -w --browser
    restart: unless-stopped

  # Local server mode
  glances-server:
    image: nicolargo/glances:latest-full
    container_name: glances-server
    ports:
      - "61209:61209"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./glances.conf:/glances/conf/glances.conf
    pid: host
    network_mode: host
    command: --config /glances/conf/glances.conf -s -B 0.0.0.0 --username glances --password yourpassword
    restart: unless-stopped

  # Export to Elasticsearch
  glances-exporter:
    image: nicolargo/glances:latest-full
    container_name: glances-exporter
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./glances.conf:/glances/conf/glances.conf
    pid: host
    network_mode: host
    command: --config /glances/conf/glances.conf --export elasticsearch --quiet
    restart: unless-stopped
```

## Elasticsearch Export Configuration

**Enhanced glances.conf for Elasticsearch:**
```ini
[elasticsearch]
host=your-elasticsearch-host
port=9200
index=glances-{hostname}
# Uses daily indices: glances-hostname-2024.01.15

[global]
refresh=5
history_size=3600
```

**Export-Only Container:**
```bash
docker run -d --name glances-export \
  --pid host \
  --network host \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ~/glances-config/glances.conf:/glances/conf/glances.conf \
  nicolargo/glances:latest-full \
  --config /glances/conf/glances.conf --export elasticsearch --quiet
```

## Container Network Considerations

**Key Container Options:**
- `--pid host`: Access host processes and system stats
- `--network host`: Direct network access (recommended for accurate stats)
- `-v /var/run/docker.sock`: Monitor Docker containers
- `-v /sys:/sys:ro`: Access hardware sensors (optional)

**Port Mapping:**
- `61208`: Web interface
- `61209`: Server mode (XML-RPC)

**Environment Variables:**
```bash
docker run -d \
  -e GLANCES_OPT="--export elasticsearch --quiet" \
  -e TZ="America/New_York" \
  nicolargo/glances:latest-full
```

## Security Best Practices

• **Always use authentication** in production
• **Bind to specific interfaces** rather than 0.0.0.0 when possible  
• **Use Docker networks** to isolate Glances traffic
• **Mount config files read-only** when possible
• **Consider using secrets** for passwords in production

The central browser approach gives you a unified dashboard showing all your monitored systems, while individual containers export metrics to your Elasticsearch cluster for long-term analysis.
