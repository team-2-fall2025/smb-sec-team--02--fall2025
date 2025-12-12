# Deployment Runbook

## Purpose
Safely deploy the SMB Security platform to the staging or production VM.

## Scope
Backend (FastAPI), Frontend (Nginx SPA), Reverse Proxy (Nginx), Database (MongoDB).

## Preconditions
- VM accessible via SSH
- Docker and Docker Compose installed
- Secrets configured via environment variables or `.env` (not in Git)
- DNS points to VM public IP

## Deployment Steps
python -m venv ".venv"
./start-app.bat