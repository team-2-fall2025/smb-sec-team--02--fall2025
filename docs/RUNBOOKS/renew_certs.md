## Purpose
Renew HTTPS certificates to maintain secure connections.

## Tool
Let's Encrypt via certbot.

## Automatic Renewal
Certbot typically runs via system timer.

Check timer:
```bash
sudo systemctl list-timers | grep certbot
```

```bash
sudo certbot renew
sudo systemctl reload nginx
```