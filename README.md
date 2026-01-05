# binhex-lab-edgegw

Unified edge gateway using Traefik v3.2 serving both lab and production services.

## Overview

This is the **single Traefik instance** routing all traffic for both lab and production environments. It provides:

- **Tenant Separation**: Lab services use `lab-*` router prefix, prod uses `prod-*/api-*`
- **Standard Ports**: 80 (HTTP) and 443 (HTTPS)
- **Multi-Network**: Connected to both `binhex-lab-edgegw` and `binhex-network`

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │     binhex-lab-edgegw-traefik       │
                    │         (ports 80/443)              │
                    └──────────────┬──────────────────────┘
                                   │
            ┌──────────────────────┴──────────────────────┐
            │                                             │
   ┌────────▼────────┐                         ┌──────────▼──────────┐
   │ binhex-lab-edgegw│                         │   binhex-network    │
   │    (lab tenant)  │                         │   (prod tenant)     │
   └─────────────────┘                         └─────────────────────┘
            │                                             │
   ┌────────┴────────┐                         ┌──────────┴──────────┐
   │  lab-phpipam    │                         │  prod-web           │
   │  lab-docs       │                         │  prod-api-main      │
   │  lab-whoami     │                         │  api-config         │
   │  lab-dashboard  │                         │  api-data           │
   └─────────────────┘                         │  api-events ...     │
                                               └─────────────────────┘
```

## Tenant Separation

| Tenant | Router Prefix | Network | Hosts |
|--------|---------------|---------|-------|
| Lab | `lab-*` | binhex-lab-edgegw | *.local |
| Prod | `prod-*`, `api-*` | binhex-network | binhex.app |

### Lab Services
- `lab-dashboard` → traefik.local (admin/changeme)
- `lab-phpipam` → phpipam.local
- `lab-docs` → docs.local
- `lab-whoami` → whoami.local

### Prod Services
- `prod-web` → binhex.app
- `prod-api-main` → binhex.app/api/main
- `api-config` → binhex.app/api/config
- `api-data` → binhex.app/api/data
- `api-policy` → binhex.app/api/policy
- `api-enforce` → binhex.app/api/enforce
- `api-events` → binhex.app/api/events
- `api-engagement` → binhex.app/api/engagement
- `api-lfg` → binhex.app/api/lfg
- `api-ops` → binhex.app/api/ops

## Quick Start

```bash
# 1. Create .env from example
cp .env.example .env

# 2. Start the gateway
docker compose up -d

# 3. Connect to prod network (if not in compose)
docker network connect binhex-network binhex-lab-edgegw-traefik

# 4. Check status
docker logs binhex-lab-edgegw-traefik
```

## Dashboard

Access the Traefik dashboard at `https://traefik.local/`

- **Username**: admin
- **Password**: changeme

Add to `/etc/hosts`:
```
127.0.0.1 traefik.local phpipam.local docs.local whoami.local binhex.app
```

## Directory Structure

```
binhex-lab-edgegw/
├── docker-compose.yml      # Main stack definition
├── traefik.yml             # Static Traefik configuration
├── .env                    # Environment configuration
├── dynamic/                # Dynamic configuration
│   ├── middlewares.yml     # Unified middlewares (lab + prod)
│   ├── tls.yml             # TLS options + certificates
│   └── services.yml        # External service definitions
├── certs/                  # TLS certificates
│   ├── server.crt/key      # Default wildcard cert
│   └── binhex.app.crt/key  # Production cert
├── examples/               # Example services
└── migration/              # Discovery manifest
```

## Adding Lab Services

Use `lab-` prefix for all router names:

```yaml
services:
  myapp:
    image: myapp:latest
    networks:
      - binhex-lab-edgegw
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=binhex-lab-edgegw"
      - "traefik.http.routers.lab-myapp.rule=Host(`myapp.local`)"
      - "traefik.http.routers.lab-myapp.entrypoints=websecure"
      - "traefik.http.routers.lab-myapp.tls=true"
      - "traefik.http.services.lab-myapp.loadbalancer.server.port=8080"

networks:
  binhex-lab-edgegw:
    external: true
```

## Adding Prod Services

Use `prod-` or `api-` prefix for router names:

```yaml
services:
  myapi:
    image: myapi:latest
    networks:
      - binhex-network
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=binhex-network"
      - "traefik.http.routers.prod-myapi.rule=Host(`binhex.app`) && PathPrefix(`/api/myapi`)"
      - "traefik.http.routers.prod-myapi.entrypoints=websecure"
      - "traefik.http.routers.prod-myapi.tls=true"
      - "traefik.http.routers.prod-myapi.middlewares=strip-api-myapi@file"
      - "traefik.http.services.prod-myapi.loadbalancer.server.port=8000"

networks:
  binhex-network:
    external: true
```

## Available Middlewares

| Middleware | Description |
|------------|-------------|
| `redirect-to-https@file` | HTTP → HTTPS redirect |
| `dashboard-auth@file` | Basic auth for dashboard |
| `security-headers@file` | Security headers (XSS, HSTS, etc.) |
| `proxy-headers@file` | X-Forwarded-Proto/Ssl headers |
| `rate-limit-default@file` | 100 req/min rate limit |
| `rate-limit-admin@file` | 30 req/min rate limit |
| `strip-api-*@file` | Path stripping for API routes |
| `compress@file` | Response compression |

## Verification

```bash
# Check all routers
curl -s -k -u admin:changeme \
  -H "Host: traefik.local" \
  https://localhost/api/http/routers | jq '.[].name'

# Test lab services
curl -k -H "Host: phpipam.local" https://localhost/
curl -k -H "Host: docs.local" https://localhost/

# Test prod services
curl -k -H "Host: binhex.app" https://localhost/
curl -k -H "Host: binhex.app" https://localhost/api/data/healthz
```

## Troubleshooting

```bash
# Check Traefik logs
docker logs binhex-lab-edgegw-traefik --tail 100

# Verify networks
docker network inspect binhex-lab-edgegw
docker network inspect binhex-network

# Check router status
curl -s -k -u admin:changeme \
  -H "Host: traefik.local" \
  https://localhost/api/http/routers | jq '.[] | {name, status}'
```

## License

MIT
