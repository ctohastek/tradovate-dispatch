# Deployment Guide

## Pre-Deployment Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Database initialized: `dispatcher.db` exists
- [ ] `.env` configured with production values
- [ ] API key secure and stored in secrets manager
- [ ] Tradovate API credentials verified
- [ ] Email/SMTP configured (if alerts enabled)
- [ ] Logs directory writable
- [ ] SSL/TLS certificate available (for HTTPS reverse proxy)

## Development Deployment

### Local Testing

```bash
python run.py
curl http://localhost:8000/health
```

## Production Deployment

### Option 1: Systemd Service (Recommended)

Create `/etc/systemd/system/tradovate-dispatch.service`:

```ini
[Unit]
Description=Tradovate Dispatch API
After=network.target

[Service]
Type=notify
User=tradovate
WorkingDirectory=/opt/tradovate-dispatch
EnvironmentFile=/opt/tradovate-dispatch/.env
ExecStart=/opt/tradovate-dispatch/venv/bin/gunicorn -c gunicorn.conf.py run:app
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl start tradovate-dispatch
sudo systemctl enable tradovate-dispatch  # Start on boot
```

### Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name dispatch.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

### Log Monitoring

```bash
tail -f logs/dispatcher.log
tail -f logs/access.log
```

## Backups

### Database Backup

```bash
cp dispatcher.db /backup/dispatcher_$(date +%Y%m%d).db
```

## Security Best Practices

1. Use TLS/SSL for all traffic
2. Store API keys in secrets manager
3. Rotate dispatcher key regularly
4. Monitor for suspicious activity
5. Keep dependencies updated
