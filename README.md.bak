# binhex-lab-edgegw

Purpose-built edge gateway using Traefik v3.2 for lab/development environments.

## Overview

This is a **NEW, separate** Traefik instance that does NOT interfere with any existing reverse proxies. It is designed for:

- Development and testing of new services
- Lab environment routing
- K8s-ready scaffolding for future migration

## Key Features

- **Isolated Network**: Uses `binhex-lab-edgegw` network (separate from production)
- **Alternative Ports**: 8080 (HTTP) and 8443 (HTTPS) by default to avoid conflicts
- **Docker Provider**: Auto-discovers containers with `traefik.enable=true`
- **File Provider**: Dynamic configuration in `/dynamic` directory
- **ACME Support**: Let's Encrypt integration with staging toggle
- **Secure Dashboard**: Protected with basic auth (no insecure mode)

## Quick Start

```bash
# 1. Create .env from example
cp .env.example .env

# 2. Edit .env with your settings
nano .env

# 3. Start the gateway
docker compose up -d

# 4. Check status
docker compose logs -f traefik
```

## Testing

```bash
# Test dashboard (with Host header)
curl -k -H "Host: traefik.local" https://localhost:8443

# Test whoami example
cd examples/whoami-http
docker compose up -d
curl -H "Host: whoami.local" http://localhost:8080

# Test HTTPS example
cd ../whoami-https
docker compose up -d
curl -k -H "Host: whoami-secure.local" https://localhost:8443
```

## Directory Structure

```
binhex-lab-edgegw/
├── docker-compose.yml      # Main stack definition
├── traefik.yml             # Static Traefik configuration
├── .env.example            # Environment template
├── dynamic/                # Dynamic configuration
│   ├── middlewares.yml     # HTTP middlewares
│   ├── tls.yml            # TLS options
│   └── services.yml       # External service definitions
├── certs/                  # Self-signed certificates
├── examples/               # Example services
│   ├── whoami-http/       # HTTP example
│   └── whoami-https/      # HTTPS example
├── migration/              # Discovery manifest
│   ├── manifest.json      # Full container analysis
│   ├── manifest.yaml      # YAML format
│   ├── manifest.md        # Human-readable summary
│   └── no_touch.md        # Containers to leave alone
└── scripts/               # Utility scripts
```

## Port Configuration

| Port | Protocol | Description |
|------|----------|-------------|
| 8080 | HTTP     | Web entrypoint (redirects to HTTPS) |
| 8443 | HTTPS    | Secure entrypoint |

To use standard ports (80/443), edit `.env`:
```bash
HTTP_PORT=80
HTTPS_PORT=443
```

## Adding Services

1. Attach container to `binhex-lab-edgegw` network
2. Add Traefik labels:

```yaml
services:
  myapp:
    image: myapp:latest
    networks:
      - binhex-lab-edgegw
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.local`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls=true"
      - "traefik.http.services.myapp.loadbalancer.server.port=8080"

networks:
  binhex-lab-edgegw:
    external: true
```

## Migration Manifest

Before migrating any services, review the discovery manifest:

- `migration/manifest.md` - Human-readable summary
- `migration/no_touch.md` - Containers that must NOT be modified

## Production Use

For production with real certificates:

1. Ensure DNS points to your server
2. Open ports 80/443 on firewall
3. Update `.env`:
   ```bash
   HTTP_PORT=80
   HTTPS_PORT=443
   STAGING=false
   ACME_EMAIL=your@email.com
   DASHBOARD_HOST=traefik.yourdomain.tld
   ```
4. Restart: `docker compose up -d`

## Troubleshooting

```bash
# Check Traefik logs
docker compose logs traefik

# Verify configuration
docker compose config

# Check routers
curl -s http://localhost:8080/api/http/routers | jq

# Check services  
curl -s http://localhost:8080/api/http/services | jq
```

## License

MIT
