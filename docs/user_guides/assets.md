# Assets Management Guide

## Quick Start

### Add Assets
**Manual:**
1. Click "Add Asset" 
2. Fill required fields (name, type, etc.)
3. Save - system auto-detects missing type/criticality

**Import:**
- Upload CSV/JSON files via "Upload CSV" button
- Supports bulk imports with auto-type detection

### Edit Assets
- Click "Edit" on any asset
- Modify fields and save
- Timestamps and intelligence links update automatically

### View Assets
- **List View**: Table with filters (name, type, owner) and sorting
- **Detail View**: Click "View" for full info + risk analysis
- **Risk Score**: Criticality × Max Intel Severity (7 days)

## Asset Types
- **HW**: Servers, routers, laptops (`server`, `vm`, `router`)
- **SW**: Apps, databases (`app`, `database`, `software`)  
- **Service**: APIs, gateways (`api`, `gateway`, `microservice`)
- **Data**: Files, logs (`data`, `file`, `backup`)
- **User**: People, teams (`user`, `admin`, `team`)

*Type auto-detected from name if not specified*

## Import Formats

**CSV:**
```csv
name,type,ip,hostname,owner,criticality
Web Server,HW,192.168.1.10,web01,IT Team,4
```

**JSON:**
```json
[{"name": "DB Server", "type": "HW", "ip": "192.168.1.20"}]
```

## Risk Scoring
- **Criticality**: 1 (Low) to 5 (Critical)
- **Intel Severity**: From linked security events
- **Risk Score**: Criticality × Max Severity