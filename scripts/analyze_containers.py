#!/usr/bin/env python3
"""
Container Analysis Script for binhex-lab-edgegw Migration Manifest
Analyzes all Docker containers and classifies them for migration planning.
"""

import subprocess
import json
import yaml
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Known reverse proxy images
REVERSE_PROXY_IMAGES = [
    'traefik', 'nginx', 'caddy', 'haproxy', 'envoy', 
    'nginx-proxy-manager', 'kong', 'istio', 'jwilder/nginx-proxy',
    'nginxproxy/nginx-proxy', 'lucaslorentz/caddy-docker-proxy'
]

# Known proxy network name patterns
PROXY_NETWORK_PATTERNS = ['traefik', 'edge', 'ingress', 'proxy', 'gateway']

# HTTP service ports
HTTP_SERVICE_PORTS = ['80', '443', '8080', '8443', '3000', '5000', '8000', '8888', '9000']

def get_all_containers() -> List[Dict]:
    """Get detailed info for all containers."""
    result = subprocess.run(
        ['docker', 'ps', '-aq'],
        capture_output=True, text=True
    )
    container_ids = result.stdout.strip().split('\n')
    container_ids = [c for c in container_ids if c]
    
    if not container_ids:
        return []
    
    result = subprocess.run(
        ['docker', 'inspect'] + container_ids,
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def get_networks() -> List[Dict]:
    """Get all Docker networks."""
    result = subprocess.run(
        ['docker', 'network', 'ls', '--format', '{{json .}}'],
        capture_output=True, text=True
    )
    networks = []
    for line in result.stdout.strip().split('\n'):
        if line:
            networks.append(json.loads(line))
    return networks

def is_reverse_proxy(container: Dict) -> bool:
    """Check if container is a reverse proxy."""
    image = container['Config']['Image'].lower()
    for proxy_image in REVERSE_PROXY_IMAGES:
        if proxy_image in image:
            return True
    
    # Check for common proxy port bindings
    ports = container.get('NetworkSettings', {}).get('Ports', {}) or {}
    has_80 = '80/tcp' in ports and ports['80/tcp']
    has_443 = '443/tcp' in ports and ports['443/tcp']
    
    # If both 80 and 443 are bound, likely a reverse proxy
    if has_80 and has_443:
        labels = container['Config'].get('Labels', {}) or {}
        # Check for traefik-specific labels on the container itself
        if 'traefik' in image or any('traefik' in k.lower() for k in labels):
            return True
    
    return False

def detect_proxy_signals(container: Dict) -> Dict[str, Any]:
    """Detect signals that indicate container is behind/using a proxy."""
    labels = container['Config'].get('Labels', {}) or {}
    env_list = container['Config'].get('Env', []) or []
    env = {}
    for e in env_list:
        if '=' in e:
            k, v = e.split('=', 1)
            env[k] = v
    
    signals = {
        'traefik_labels': {},
        'nginx_proxy_env': {},
        'caddy_labels': {},
        'has_proxy_signals': False
    }
    
    # Traefik labels
    for k, v in labels.items():
        if k.startswith('traefik.'):
            signals['traefik_labels'][k] = v
            signals['has_proxy_signals'] = True
    
    # nginx-proxy environment variables
    nginx_proxy_vars = ['VIRTUAL_HOST', 'VIRTUAL_PORT', 'LETSENCRYPT_HOST', 'LETSENCRYPT_EMAIL']
    for var in nginx_proxy_vars:
        if var in env:
            signals['nginx_proxy_env'][var] = env[var]
            signals['has_proxy_signals'] = True
    
    # Caddy labels
    for k, v in labels.items():
        if k.startswith('caddy') or 'caddy.reverse_proxy' in k.lower():
            signals['caddy_labels'][k] = v
            signals['has_proxy_signals'] = True
    
    return signals

def get_published_ports(container: Dict) -> Dict[str, List[str]]:
    """Get host-published ports."""
    ports_config = container.get('NetworkSettings', {}).get('Ports', {}) or {}
    published = {}
    for port, bindings in ports_config.items():
        if bindings:
            published[port] = [f"{b['HostIp']}:{b['HostPort']}" for b in bindings]
    return published

def get_exposed_ports(container: Dict) -> List[str]:
    """Get container-exposed ports (not necessarily published)."""
    exposed = container['Config'].get('ExposedPorts', {}) or {}
    return list(exposed.keys())

def is_in_proxy_network(networks: List[str]) -> bool:
    """Check if container is in a known proxy network."""
    for net in networks:
        for pattern in PROXY_NETWORK_PATTERNS:
            if pattern in net.lower():
                return True
    return False

def classify_container(container: Dict) -> str:
    """
    Classify a container into one of:
    - already_proxied_traefik
    - already_proxied_other
    - exposed_directly
    - internal_only
    - unknown_needs_review
    """
    proxy_signals = detect_proxy_signals(container)
    published_ports = get_published_ports(container)
    networks = list((container.get('NetworkSettings', {}).get('Networks', {}) or {}).keys())
    
    # Check for Traefik proxy signals
    if proxy_signals['traefik_labels']:
        traefik_enabled = proxy_signals['traefik_labels'].get('traefik.enable', '').lower() == 'true'
        if traefik_enabled or is_in_proxy_network(networks):
            return 'already_proxied_traefik'
    
    # Check for nginx-proxy or caddy signals
    if proxy_signals['nginx_proxy_env'] or proxy_signals['caddy_labels']:
        return 'already_proxied_other'
    
    # Check if exposed directly (has published ports, no proxy signals)
    if published_ports and not proxy_signals['has_proxy_signals']:
        return 'exposed_directly'
    
    # Check if internal only
    if not published_ports and not proxy_signals['has_proxy_signals']:
        return 'internal_only'
    
    return 'unknown_needs_review'

def is_http_service(container: Dict) -> bool:
    """Check if container likely serves HTTP traffic."""
    image = container['Config']['Image'].lower()
    exposed = get_exposed_ports(container)
    
    # Check exposed ports for HTTP-like ports
    for port in exposed:
        port_num = port.split('/')[0]
        if port_num in HTTP_SERVICE_PORTS:
            return True
    
    # Check image name for web service patterns
    web_patterns = ['web', 'api', 'http', 'nginx', 'apache', 'flask', 'django', 'express', 'node', 'react', 'next']
    for pattern in web_patterns:
        if pattern in image:
            return True
    
    return False

def generate_recommended_labels(container: Dict) -> Dict[str, str]:
    """Generate recommended Traefik labels for migration."""
    name = container['Name'].lstrip('/')
    safe_name = name.replace('-', '_').replace('.', '_')
    
    exposed = get_exposed_ports(container)
    port = '80'
    for p in exposed:
        port_num = p.split('/')[0]
        if port_num in HTTP_SERVICE_PORTS:
            port = port_num
            break
    
    return {
        'traefik.enable': 'true',
        f'traefik.http.routers.{safe_name}.rule': f'Host(`{name}.local`)',
        f'traefik.http.routers.{safe_name}.entrypoints': 'websecure',
        f'traefik.http.routers.{safe_name}.tls': 'true',
        f'traefik.http.services.{safe_name}.loadbalancer.server.port': port
    }

def is_candidate_for_migration(container: Dict, classification: str) -> tuple:
    """Determine if container is a candidate for migration and why."""
    name = container['Name'].lstrip('/')
    
    # Never migrate reverse proxies themselves
    if is_reverse_proxy(container):
        return False, 'Container is a reverse proxy'
    
    # Never migrate already proxied containers
    if classification.startswith('already_proxied'):
        return False, f'Already proxied ({classification})'
    
    # Candidate if exposed directly and is HTTP service
    if classification == 'exposed_directly':
        if is_http_service(container):
            return True, 'HTTP service exposed directly - good migration candidate'
        else:
            return False, 'Exposed directly but not an HTTP service'
    
    # Candidate if internal but is HTTP service (could benefit from proxy)
    if classification == 'internal_only':
        if is_http_service(container):
            return True, 'Internal HTTP service - could benefit from proxy exposure'
        else:
            return False, 'Internal service, not HTTP'
    
    return False, 'Needs manual review'

def analyze_risks(container: Dict, published_ports: Dict) -> List[str]:
    """Analyze risks/notes for migration."""
    risks = []
    
    # Multiple ports
    if len(published_ports) > 1:
        risks.append('Multiple published ports - may need separate routers')
    
    # Non-standard ports
    exposed = get_exposed_ports(container)
    for port in exposed:
        port_num = port.split('/')[0]
        if port_num not in HTTP_SERVICE_PORTS:
            risks.append(f'Non-HTTP port {port_num} - may need TCP/UDP router')
    
    # Check for auth requirements
    labels = container['Config'].get('Labels', {}) or {}
    if any('auth' in k.lower() for k in labels):
        risks.append('May have authentication requirements')
    
    # Check for stateful services
    image = container['Config']['Image'].lower()
    stateful = ['postgres', 'mysql', 'mariadb', 'redis', 'mongo', 'elasticsearch']
    for svc in stateful:
        if svc in image:
            risks.append('Stateful database service - typically not proxied')
    
    return risks

def main():
    print("Analyzing Docker containers...")
    
    containers = get_all_containers()
    networks = get_networks()
    
    reverse_proxies = []
    inventory = []
    
    for container in containers:
        c_id = container['Id'][:12]
        name = container['Name'].lstrip('/')
        image = container['Config']['Image']
        status = container['State']['Status']
        container_networks = list((container.get('NetworkSettings', {}).get('Networks', {}) or {}).keys())
        
        # Check if this is a reverse proxy
        if is_reverse_proxy(container):
            published = get_published_ports(container)
            reverse_proxies.append({
                'container_id': c_id,
                'container_name': name,
                'image': image,
                'status': status,
                'networks': container_networks,
                'published_ports': published
            })
            continue
        
        # Analyze container
        proxy_signals = detect_proxy_signals(container)
        published_ports = get_published_ports(container)
        exposed_ports = get_exposed_ports(container)
        classification = classify_container(container)
        is_candidate, reason = is_candidate_for_migration(container, classification)
        risks = analyze_risks(container, published_ports)
        
        entry = {
            'container_id': c_id,
            'container_name': name,
            'image': image,
            'status': status,
            'networks': container_networks,
            'published_ports': published_ports,
            'exposed_ports': exposed_ports,
            'detected_proxy_signals': proxy_signals,
            'classification': classification,
            'candidate_for_migration': is_candidate,
            'migration_reason': reason,
            'recommended_labels': generate_recommended_labels(container) if is_candidate else {},
            'recommended_hostnames': [f'{name}.local'] if is_candidate else [],
            'risks_notes': risks
        }
        inventory.append(entry)
    
    # Build manifest
    manifest = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'summary': {
            'total_containers': len(inventory),
            'reverse_proxies_detected': len(reverse_proxies),
            'by_classification': {},
            'migration_candidates': 0
        },
        'reverse_proxies': reverse_proxies,
        'containers': inventory
    }
    
    # Count by classification
    for entry in inventory:
        cls = entry['classification']
        manifest['summary']['by_classification'][cls] = manifest['summary']['by_classification'].get(cls, 0) + 1
        if entry['candidate_for_migration']:
            manifest['summary']['migration_candidates'] += 1
    
    # Write JSON
    os.makedirs('/projects/binhex-lab-edgegw/migration', exist_ok=True)
    
    with open('/projects/binhex-lab-edgegw/migration/manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Write YAML
    with open('/projects/binhex-lab-edgegw/migration/manifest.yaml', 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    # Write Markdown summary
    md_lines = [
        '# Migration Manifest',
        f'Generated: {manifest["generated_at"]}',
        '',
        '## Summary',
        f'- **Total Containers Analyzed**: {manifest["summary"]["total_containers"]}',
        f'- **Reverse Proxies Detected**: {manifest["summary"]["reverse_proxies_detected"]}',
        f'- **Migration Candidates**: {manifest["summary"]["migration_candidates"]}',
        '',
        '### Classification Breakdown',
    ]
    
    for cls, count in manifest['summary']['by_classification'].items():
        md_lines.append(f'- {cls}: {count}')
    
    md_lines.extend(['', '## Detected Reverse Proxies', ''])
    md_lines.append('| Container | Image | Ports | Networks |')
    md_lines.append('|-----------|-------|-------|----------|')
    for rp in reverse_proxies:
        ports = ', '.join([f'{p}' for p in rp['published_ports'].keys()])
        nets = ', '.join(rp['networks'])
        md_lines.append(f"| {rp['container_name']} | {rp['image']} | {ports} | {nets} |")
    
    md_lines.extend(['', '## Migration Candidates', ''])
    md_lines.append('| Container | Image | Classification | Reason |')
    md_lines.append('|-----------|-------|----------------|--------|')
    for entry in inventory:
        if entry['candidate_for_migration']:
            md_lines.append(f"| {entry['container_name']} | {entry['image'][:40]} | {entry['classification']} | {entry['migration_reason']} |")
    
    md_lines.extend(['', '## All Containers', ''])
    md_lines.append('| Container | Classification | Candidate | Notes |')
    md_lines.append('|-----------|----------------|-----------|-------|')
    for entry in inventory:
        candidate = '✓' if entry['candidate_for_migration'] else '✗'
        notes = '; '.join(entry['risks_notes'][:2]) if entry['risks_notes'] else '-'
        md_lines.append(f"| {entry['container_name']} | {entry['classification']} | {candidate} | {notes[:50]} |")
    
    with open('/projects/binhex-lab-edgegw/migration/manifest.md', 'w') as f:
        f.write('\n'.join(md_lines))
    
    # Generate no-touch list
    no_touch_lines = [
        '# No-Touch List',
        '',
        'These containers are already proxied and MUST NOT be modified by binhex-lab-edgegw migration.',
        '',
        '## Already Proxied Containers',
        '',
        '| Container | Current Proxy | Network | Traefik Labels |',
        '|-----------|---------------|---------|----------------|'
    ]
    
    for entry in inventory:
        if entry['classification'].startswith('already_proxied'):
            labels = entry['detected_proxy_signals']['traefik_labels']
            label_summary = 'traefik.enable=true' if labels else 'nginx-proxy/caddy'
            nets = ', '.join(entry['networks'])
            no_touch_lines.append(f"| {entry['container_name']} | {entry['classification'].replace('already_proxied_', '')} | {nets} | {label_summary} |")
    
    no_touch_lines.extend([
        '',
        '## Reverse Proxies',
        '',
        '| Container | Image | Ports |',
        '|-----------|-------|-------|'
    ])
    
    for rp in reverse_proxies:
        ports = ', '.join([f'{p}' for p in rp['published_ports'].keys()])
        no_touch_lines.append(f"| {rp['container_name']} | {rp['image']} | {ports} |")
    
    no_touch_lines.extend([
        '',
        '---',
        '',
        '**IMPORTANT**: The binhex-lab-edgegw gateway DOES NOT and WILL NOT modify these containers.',
        'Any migration must be an explicit, opt-in process performed manually.'
    ])
    
    with open('/projects/binhex-lab-edgegw/migration/no_touch.md', 'w') as f:
        f.write('\n'.join(no_touch_lines))
    
    print(f"\nManifest files generated:")
    print("  - /projects/binhex-lab-edgegw/migration/manifest.json")
    print("  - /projects/binhex-lab-edgegw/migration/manifest.yaml")
    print("  - /projects/binhex-lab-edgegw/migration/manifest.md")
    print("  - /projects/binhex-lab-edgegw/migration/no_touch.md")
    
    print(f"\n=== Summary ===")
    print(f"Reverse Proxies Detected: {len(reverse_proxies)}")
    for rp in reverse_proxies:
        print(f"  - {rp['container_name']} ({rp['image']}) on ports {list(rp['published_ports'].keys())}")
    
    print(f"\nContainers by Classification:")
    for cls, count in manifest['summary']['by_classification'].items():
        print(f"  - {cls}: {count}")
    
    print(f"\nMigration Candidates: {manifest['summary']['migration_candidates']}")

if __name__ == '__main__':
    main()
