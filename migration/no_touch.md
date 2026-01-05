# No-Touch List

**Generated**: 2026-01-05T05:54:50Z

These containers are already proxied and **MUST NOT** be modified by binhex-lab-edgegw migration.

## Already Proxied Containers

The following containers are served by the existing `binhex-edge-proxy` (Traefik v3.2) instance on `binhex-network`.

| Container | Current Proxy | Network | Router | Host |
|-----------|---------------|---------|--------|------|
| binhex-ops-api | traefik | binhex-network | api-admin-ops | binhex.app |
| binhex-web | traefik | binhex-network | web | binhex.app |
| binhex-api | traefik | binhex-network | api-main | binhex.app |
| binhex-events-service | traefik | binhex-network | api-events | binhex.app |
| binhex-worker | traefik | binhex-network | api-ops | binhex.app |
| binhex-lfg-service | traefik | binhex-network | api-lfg | binhex.app |
| engagement-service | traefik | binhex-network | api-engagement | binhex.app |
| policy-service | traefik | binhex-network | api-policy | binhex.app |
| binhex-enforcement | traefik | binhex-network | api-enforce | binhex.app |
| binhex-config-api | traefik | binhex-network | api-config | binhex.app |
| binhex-data-api | traefik | binhex-network | api-data | binhex.app |

## Reverse Proxies

The following reverse proxy instances exist in the environment:

| Container | Image | Ports | Network |
|-----------|-------|-------|---------|
| binhex-edge-proxy | traefik:v3.2 | 80/tcp, 443/tcp | binhex-network |

## Protected Resources

### Networks
- `binhex-network` - Primary network for binhex-stack services

### Configuration Files
- `/projects/binhex-stack/services/edge-proxy/traefik.yml`
- `/projects/binhex-stack/services/edge-proxy/dynamic/`
- `/projects/binhex-stack/services/edge-proxy/certs/`

---

## Guarantee

**IMPORTANT**: The `binhex-lab-edgegw` gateway:

1. **DOES NOT** modify any containers listed above
2. **DOES NOT** change labels on existing containers
3. **DOES NOT** attach containers to new networks without explicit user action
4. **DOES NOT** modify the `binhex-network` or any existing proxy networks
5. **DOES NOT** conflict with ports 80/443 already bound by `binhex-edge-proxy`

The new gateway uses:
- **Separate network**: `binhex-lab-edgegw`
- **Separate ports**: Configurable (default: 8080/8443 or alternative)
- **Separate configuration**: `/projects/binhex-lab-edgegw/`

Any migration to `binhex-lab-edgegw` must be:
1. Explicitly documented
2. Manually approved
3. Separately executed

This is a **read-only discovery** - no changes have been made to any existing services.
