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

Production-ready nginx vhost configuration for Tradovate Dispatch. This configuration:

- **Uses basic HTTP authentication** — requires creation of an `.htpasswd` style file (see setup below)
- **Tested and working on Fedora variants** — verified on Fedora CoreOS and similar distributions
- Enforces HTTPS/TLS 1.2+ with modern ciphers
- Implements rate limiting at the nginx level
- Proxies to gunicorn on localhost:8000
- Includes security headers and connection limits

#### Setup Steps

1. **Create `.htpasswd` file** for basic auth:
   ```bash
   sudo htpasswd -c /etc/nginx/.htpasswd-dispatch username
   # Follow prompts to set password
   ```

2. **Place SSL certificates** at the paths specified in the config:
   - `/path/to/domain.crt` — public certificate
   - `/path/to/domain.key` — private key
   - `/path/to/domain.rootchain` — root/intermediate chain

3. **Install nginx configuration** in `/etc/nginx/conf.d/tradovate-dispatch.conf` or `/etc/nginx/sites-available/tradovate-dispatch.conf`

#### Configuration

```nginx
# nginx reverse proxy — Tradovate Dispatch
#
# gunicorn listens on 127.0.0.1:8000 (internal only)

# ── Rate Limiting Zones ──
# 10 requests/sec per IP for pages, 30/sec for API, 3/min for login failures
limit_req_zone $binary_remote_addr zone=si_dispatch:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=si_execute:10m     rate=30r/s;
#limit_req_zone $binary_remote_addr zone=si_auth:10m    rate=3r/m;

# ── Upstream (gunicorn on localhost:8000) ──
upstream tradovate-dispatch{
    server 127.0.0.1:8000;
    keepalive 4;
}

# ── HTTPS vhost port 443 ──
server {
    listen 443 ssl;
    http2 on;    
    server_name tradovate-dispatch.hastek.net;

    # ── SSL ──
    ssl_certificate     /path/to/domain.crt;
    ssl_certificate_key /path/to/domain.key;
    ssl_trusted_certificate /path/to/domain.rootchain;

    # Modern TLS
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # OCSP stapling
    # ssl_stapling on;
    # ssl_stapling_verify on;
    # resolver 8.8.8.8 1.1.1.1 valid=300s;

    # ── Security Headers ──
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # ── Connection limits ──
    client_max_body_size 1m;
    client_body_timeout 10s;
    client_header_timeout 10s;
    send_timeout 10s;
    keepalive_timeout 30s;

    # ── Proxy to gunicorn ──
    location / {
        auth_basic "tradovate-dispatch login";
        auth_basic_user_file /etc/nginx/.htpasswd-dispatch;
        # Rate limit: 10 req/s, burst 10
        limit_req zone=si_dispatch burst=10 nodelay;
        limit_req_status 429;

        proxy_pass http://tradovate-dispatch;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 300s;  # long for /api/poll
        proxy_send_timeout 10s;

        # Buffer responses (protects gunicorn from slow clients)
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 8k;
    }

    # Higher rate limit for API endpoints
    location /execute/ {
        auth_basic "tradovate-dispatch login";
        auth_basic_user_file /etc/nginx/.htpasswd-dispatch;
        limit_req zone=si_execute burst=10 nodelay;
        limit_req_status 429;

        proxy_pass http://tradovate-dispatch;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Strict rate limit on auth failures (fail2ban also catches these)
    error_page 401 @auth_limited;
    location @auth_limited {
        limit_req zone=si_auth burst=5;
        return 401;
    }

    # Block common scanners
    location ~* (\.php|\.asp|\.aspx|\.jsp|\.cgi|wp-admin|wp-login) {
        return 444;
    }

    # ── Logging ──
    access_log /var/log/nginx/tradovate-dispatch-access.log;
    error_log  /var/log/nginx/tradovate-dispatch-error.log;
}
```

## Mail sending/relay
This app can be configured to send emails. To ensure success, send using your own relay or one such as Proton Mail Bridge from a host with proper DNS/reverseDNS, SPF, DKIM etc configurations.

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
