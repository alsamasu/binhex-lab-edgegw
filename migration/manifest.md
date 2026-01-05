# Migration Manifest

**Generated**: 2026-01-05T05:54:50Z

## Summary

| Metric | Count |
|--------|-------|
| Total Containers Analyzed | 24 |
| Reverse Proxies Detected | 1 |
| Migration Candidates | 3 |

### Classification Breakdown

| Classification | Count |
|----------------|-------|
| already_proxied_traefik | 11 |
| internal_only | 8 |
| exposed_directly | 5 |

## Detected Reverse Proxies

| Container | Image | Ports | Networks |
|-----------|-------|-------|----------|
| binhex-edge-proxy | traefik:v3.2 | 80/tcp, 443/tcp | binhex-network |

> **Note**: The existing `binhex-edge-proxy` Traefik instance will NOT be modified by this migration. The new `binhex-lab-edgegw` stack is a completely separate gateway.

## Migration Candidates

These containers are candidates for migration to `binhex-lab-edgegw`:

| Container | Image | Classification | Reason |
|-----------|-------|----------------|--------|
| phpipam-web | phpipam/phpipam-www:latest | exposed_directly | HTTP service exposed directly - good migration candidate |
| phpipam-cron | phpipam/phpipam-cron:latest | internal_only | Internal HTTP service - could benefit from proxy exposure |
| mkdocs-serve | python:3.11-slim | exposed_directly | HTTP service exposed directly - good migration candidate |

### Recommended Labels for Migration

#### phpipam-web
```yaml
labels:
  traefik.enable: "true"
  traefik.http.routers.phpipam_web.rule: "Host(`phpipam-web.local`)"
  traefik.http.routers.phpipam_web.entrypoints: "websecure"
  traefik.http.routers.phpipam_web.tls: "true"
  traefik.http.services.phpipam_web.loadbalancer.server.port: "80"
networks:
  - binhex-lab-edgegw
```

#### phpipam-cron
```yaml
labels:
  traefik.enable: "true"
  traefik.http.routers.phpipam_cron.rule: "Host(`phpipam-cron.local`)"
  traefik.http.routers.phpipam_cron.entrypoints: "websecure"
  traefik.http.routers.phpipam_cron.tls: "true"
  traefik.http.services.phpipam_cron.loadbalancer.server.port: "80"
networks:
  - binhex-lab-edgegw
```

#### mkdocs-serve
```yaml
labels:
  traefik.enable: "true"
  traefik.http.routers.mkdocs_serve.rule: "Host(`mkdocs-serve.local`)"
  traefik.http.routers.mkdocs_serve.entrypoints: "websecure"
  traefik.http.routers.mkdocs_serve.tls: "true"
  traefik.http.services.mkdocs_serve.loadbalancer.server.port: "8000"
networks:
  - binhex-lab-edgegw
```

## All Containers

| Container | Classification | Candidate | Notes |
|-----------|----------------|-----------|-------|
| pykmip-server | exposed_directly | ✗ | Non-HTTP port 5696 - KMIP protocol |
| binhex-tools | exposed_directly | ✗ | Non-HTTP port 8788 - internal MCP API |
| serene_engelbart | internal_only | ✗ | MCP Docker helper |
| phpipam-web | exposed_directly | ✓ | HTTP on port 80 |
| phpipam-cron | internal_only | ✓ | HTTP on port 80 |
| phpipam-db | internal_only | ✗ | MariaDB database |
| binhex-ops-api | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-bot | internal_only | ✗ | Discord bot |
| binhex-web | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| cisco-console | exposed_directly | ✗ | Serial console bridge |
| binhex-api | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-events-service | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-worker | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-lfg-service | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| engagement-service | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| policy-service | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-enforcement | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-config-api | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-data-api | already_proxied_traefik | ✗ | Via binhex-edge-proxy |
| binhex-db | internal_only | ✗ | PostgreSQL database |
| binhex-redis | internal_only | ✗ | Redis cache |
| mkdocs-serve | exposed_directly | ✓ | HTTP docs server |
| binhex-dev | internal_only | ✗ | Development container |
| binhex-mcp | internal_only | ✗ | MCP stdio proxy |

---

## Important Notes

1. **No automatic migration**: This manifest is for planning only. No containers will be automatically migrated.
2. **Explicit opt-in required**: Each migration must be explicitly approved and executed.
3. **Network isolation**: Containers must be manually attached to `binhex-lab-edgegw` network.
4. **Port conflicts**: Remove host port bindings when migrating to avoid conflicts.
