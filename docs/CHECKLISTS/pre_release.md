## Security
- [ ] SAST & SCA CI passing (Bandit, pip-audit, npm audit)
- [ ] DAST (OWASP ZAP) no unhandled HIGH alerts
- [ ] Trivy scan no CRITICAL findings
- [ ] Secrets scan clean

## Platform
- [ ] Reverse proxy configured
- [ ] TLS enabled and valid
- [ ] Security headers verified

## Reliability
- [ ] DB indexes applied
- [ ] Scheduler lock & retries enabled
- [ ] Load test meets thresholds

## Observability
- [ ] Structured logs enabled
- [ ] X-Request-ID present
- [ ] /health and /version endpoints live

## Release
- [ ] Backups verified
- [ ] Rollback plan reviewed
- [ ] Team sign-off