# 🚀 Deployment Guide - CSL Corner Prediction System

## Overview

This guide provides comprehensive instructions for deploying the China Super League Corner Prediction System in various environments, from development to production.

---

## 📋 Pre-Deployment Checklist

### System Requirements

#### **Minimum Requirements**
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 10 GB free space
- **OS**: Windows 10/11, Ubuntu 18.04+, macOS 10.14+
- **Python**: 3.9 or higher
- **Network**: Stable internet connection for API calls

#### **Recommended Requirements**
- **CPU**: 4 cores, 2.5 GHz
- **RAM**: 8 GB
- **Storage**: 20 GB free space (SSD preferred)
- **OS**: Latest stable versions
- **Python**: 3.11 or higher
- **Network**: High-speed internet (API-intensive application)

### Dependencies Verification

```bash
# Check Python version
python --version
# Should be 3.9 or higher

# Check pip availability
pip --version

# Check virtual environment capability
python -m venv --help
```

---

## 🔧 Local Development Deployment

### Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd corners

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup season data (one command does everything)
python setup_season.py 2025  # Current season
# OR
python setup_season.py 2024  # Completed season

# 6. Run application
python app.py

# Alternative: Quick start (all-in-one)
python quick_start.py --season 2025
```

### Development Configuration

Create `config_dev.py` for development-specific settings:

```python
from config import Config

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Development database
    DATABASE_PATH = 'corners_dev.db'
    
    # Relaxed rate limiting for testing
    API_CALLS_PER_MINUTE = 500
    
    # Shorter cache timeout for development
    CACHE_TIMEOUT_HOURS = 1
    
    # Enable detailed logging
    LOG_LEVEL = 'DEBUG'
```

### Development Testing

```bash
# Test season setup
python setup_season.py 2025  # Should complete successfully
python check_csl_seasons.py  # Should show available seasons

# Test basic functionality
curl http://localhost:5000/api/status

# Test prediction endpoint (use actual team IDs from your season)
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team_id": 1, "away_team_id": 2, "season": 2025}'

# Test web interface
# Navigate to http://localhost:5000 in browser

# Test quick start
python quick_start.py --season 2025  # Should setup and launch
```

---

## 🏭 Production Deployment

### Option 1: Traditional Server Deployment

#### **Ubuntu/Debian Server Setup**

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# 3. Create application user
sudo useradd -m -s /bin/bash cslpredictions
sudo su - cslpredictions

# 4. Clone and setup application
git clone <repository-url> /home/cslpredictions/corners
cd /home/cslpredictions/corners

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Setup production season data
python setup_season.py 2025  # Current season for production
# This automatically initializes database and imports all necessary data
```

#### **Production Configuration**

Create `config_prod.py`:

```python
import os
from config import Config

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Production database
    DATABASE_PATH = '/home/cslpredictions/data/corners_production.db'
    
    # Strict rate limiting
    API_CALLS_PER_DAY = 7000  # Leave buffer
    API_CALLS_PER_MINUTE = 250  # Leave buffer
    
    # Longer cache for production
    CACHE_TIMEOUT_HOURS = 12
    
    # Production logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/home/cslpredictions/logs/app.log'
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    @staticmethod
    def init_app(app):
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('/home/cslpredictions/logs'):
            os.makedirs('/home/cslpredictions/logs')
        
        file_handler = RotatingFileHandler(
            ProductionConfig.LOG_FILE,
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CSL Predictions startup')
```

#### **Gunicorn Configuration**

Create `gunicorn_config.py`:

```python
# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/home/cslpredictions/logs/gunicorn_access.log"
errorlog = "/home/cslpredictions/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "csl_predictions"

# Daemon mode
daemon = False
pidfile = "/home/cslpredictions/gunicorn.pid"
user = "cslpredictions"
group = "cslpredictions"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

#### **Supervisor Configuration**

Create `/etc/supervisor/conf.d/cslpredictions.conf`:

```ini
[program:cslpredictions]
command=/home/cslpredictions/corners/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/home/cslpredictions/corners
user=cslpredictions
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/cslpredictions/logs/supervisor.log
environment=FLASK_ENV=production
```

#### **Nginx Configuration**

Create `/etc/nginx/sites-available/cslpredictions`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static {
        alias /home/cslpredictions/corners/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

#### **SSL Configuration (Optional but Recommended)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

#### **Start Production Services**

```bash
# Enable and start services
sudo systemctl enable nginx
sudo systemctl enable supervisor

sudo systemctl start nginx
sudo systemctl start supervisor

# Start application
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cslpredictions

# Check status
sudo supervisorctl status
sudo nginx -t
sudo systemctl status nginx
```

### Option 2: Docker Deployment

#### **Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Initialize database
RUN python -c "from data.database import get_db_manager; get_db_manager().create_tables()"

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Run application
CMD ["python", "app.py"]
```

#### **Docker Compose**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  csl-predictions:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - csl-predictions
    restart: unless-stopped

volumes:
  data:
  logs:
```

#### **Docker Deployment Commands**

```bash
# Build and start
docker-compose up -d

# Setup season data in container
docker-compose exec csl-predictions python setup_season.py 2025

# View logs
docker-compose logs -f

# Scale application (if needed)
docker-compose up -d --scale csl-predictions=3

# Update application
docker-compose pull
docker-compose up -d

# Backup data
docker-compose exec csl-predictions cp /app/corners_prediction.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db
```

### Option 3: Cloud Deployment

#### **AWS EC2 Deployment**

```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. Configure security groups (ports 22, 80, 443)
# 3. SSH to instance

ssh -i your-key.pem ubuntu@your-ec2-instance

# 4. Follow Ubuntu deployment steps above
# 5. Configure Elastic Load Balancer (optional)
# 6. Set up CloudWatch monitoring (optional)
```

#### **Google Cloud Platform**

```bash
# 1. Create Compute Engine instance
gcloud compute instances create csl-predictions \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud

# 2. SSH to instance
gcloud compute ssh csl-predictions

# 3. Follow Ubuntu deployment steps
# 4. Configure load balancer and monitoring
```

#### **DigitalOcean Droplet**

```bash
# 1. Create droplet (2GB RAM minimum)
# 2. SSH to droplet
# 3. Follow Ubuntu deployment steps
# 4. Configure firewall and monitoring
```

---

## 🔄 Season Management

### Dynamic Season Setup

The system now includes dynamic season management tools that make it easy to work with any CSL season:

#### **Available Tools**

| Tool | Purpose | Usage |
|------|---------|-------|
| `setup_season.py` | Setup any season data | `python setup_season.py 2025` |
| `check_csl_seasons.py` | Check available seasons | `python check_csl_seasons.py` |
| `quick_start.py` | All-in-one setup and launch | `python quick_start.py --season 2025` |

#### **Season Setup Process**

```bash
# 1. Check what seasons are available
python check_csl_seasons.py

# Output shows:
# 🔥 CURRENT SEASON: 2025 (February 22, 2025 to November 22, 2025)
# 📚 Recent seasons available: [2024, 2023, 2022, 2021]

# 2. Setup the season you want
python setup_season.py 2025  # Current season with fresh data
python setup_season.py 2024  # Completed season with full data

# 3. Run the application
python app.py
```

#### **Production Season Management**

```bash
# Production setup with current season
python setup_season.py 2025

# Force refresh of season data
python setup_season.py 2025 --force

# Check data quality
python -c "
from data.database import get_db_manager
db = get_db_manager()
with db.get_connection() as conn:
    cursor = conn.execute('SELECT season, COUNT(*) as teams FROM teams GROUP BY season')
    for season, count in cursor.fetchall():
        cursor2 = conn.execute('SELECT COUNT(*) FROM matches WHERE season = ? AND corners_home IS NOT NULL', (season,))
        corner_matches = cursor2.fetchone()[0]
        print(f'Season {season}: {count} teams, {corner_matches} matches with corner data')
"
```

#### **Automated Season Updates**

For production environments, you can automate season updates:

```bash
# Create update script
cat > update_season.sh << 'EOF'
#!/bin/bash
cd /path/to/corners
source venv/bin/activate

# Get current year
CURRENT_YEAR=$(date +%Y)

# Update current season data
python setup_season.py $CURRENT_YEAR --force

# Restart application (adjust for your deployment)
sudo supervisorctl restart cslpredictions
EOF

chmod +x update_season.sh

# Add to crontab for weekly updates
crontab -e
# Add: 0 2 * * 1 /path/to/update_season.sh
```

#### **Multi-Season Support**

The system can handle multiple seasons simultaneously:

```bash
# Setup multiple seasons for comparison
python setup_season.py 2025  # Current season
python setup_season.py 2024  # Previous season
python setup_season.py 2023  # Historical data

# The web interface will automatically detect all available seasons
```

---

## 🔐 Security Configuration

### Application Security

```python
# Add to config.py
class ProductionConfig(Config):
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
```

### System Security

```bash
# Firewall configuration
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Fail2ban for SSH protection
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Regular updates
sudo apt update && sudo apt upgrade -y

# Log monitoring
sudo apt install logwatch -y
```

### Database Security

```bash
# Secure database file permissions
chmod 600 /path/to/corners_prediction.db
chown cslpredictions:cslpredictions /path/to/corners_prediction.db

# Regular backups
crontab -e
# Add: 0 2 * * * cp /path/to/corners_prediction.db /path/to/backups/corners_$(date +\%Y\%m\%d).db
```

---

## 📊 Monitoring & Maintenance

### Application Monitoring

#### **Health Check Endpoint**

The system includes a built-in health check:

```bash
# Check application health
curl http://localhost:5000/api/status

# Expected response:
{
  "status": "success",
  "message": "System operational",
  "data": {
    "api_health": "Healthy",
    "database": {"status": "Connected"},
    "cache": {"status": "Active"}
  }
}
```

#### **Log Monitoring**

```bash
# Application logs
tail -f /home/cslpredictions/logs/app.log

# Gunicorn logs
tail -f /home/cslpredictions/logs/gunicorn_error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Supervisor logs
sudo tail -f /var/log/supervisor/supervisord.log
```

#### **Performance Monitoring**

Create monitoring script `monitor.sh`:

```bash
#!/bin/bash

# Check application response time
response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:5000/api/status)
echo "Response time: ${response_time}s"

# Check memory usage
memory_usage=$(ps aux | grep python | grep app.py | awk '{print $4}')
echo "Memory usage: ${memory_usage}%"

# Check disk usage
disk_usage=$(df -h / | awk 'NR==2{print $5}')
echo "Disk usage: ${disk_usage}"

# Check API rate limits
api_status=$(curl -s http://localhost:5000/api/status | jq -r '.data.rate_limits.calls_today')
echo "API calls today: ${api_status}"
```

### Automated Backups

Create backup script `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/cslpredictions/backups"
DB_PATH="/home/cslpredictions/data/corners_production.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp $DB_PATH "$BACKUP_DIR/corners_$DATE.db"

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /home/cslpredictions/logs/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "corners_*.db" -mtime +30 -delete
find $BACKUP_DIR -name "logs_*.tar.gz" -mtime +30 -delete

echo "Backup completed: corners_$DATE.db"
```

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /home/cslpredictions/backup.sh
```

### System Updates

Create update script `update.sh`:

```bash
#!/bin/bash

cd /home/cslpredictions/corners

# Backup current version
cp corners_production.db backups/pre_update_$(date +%Y%m%d).db

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart application
sudo supervisorctl restart cslpredictions

echo "Update completed successfully"
```

---

## 🚨 Troubleshooting

### Common Issues

#### **Application Won't Start**

```bash
# Check Python path
which python
python --version

# Check virtual environment
source venv/bin/activate
which python

# Check dependencies
pip list
pip install -r requirements.txt

# Check database
python -c "from data.database import get_db_manager; print('DB OK')"

# Check logs
tail -f logs/app.log
```

#### **High Memory Usage**

```bash
# Check memory usage
ps aux | grep python | head -10

# Restart application
sudo supervisorctl restart cslpredictions

# Check for memory leaks
python -c "
import tracemalloc
tracemalloc.start()
# Your application code
current, peak = tracemalloc.get_traced_memory()
print(f'Current memory usage: {current / 1024 / 1024:.1f} MB')
print(f'Peak memory usage: {peak / 1024 / 1024:.1f} MB')
"
```

#### **API Rate Limits Exceeded**

```bash
# Check current usage
curl http://localhost:5000/api/status | jq '.data.rate_limits'

# Wait for reset (daily limit resets at midnight UTC)
# Or implement request queuing in application
```

#### **Database Issues**

```bash
# Check database file
ls -la corners_production.db

# Test database connection
python -c "
from data.database import get_db_manager
db = get_db_manager()
with db.get_connection() as conn:
    cursor = conn.execute('SELECT COUNT(*) FROM teams')
    print(f'Teams in database: {cursor.fetchone()[0]}')
"

# Backup and recreate if corrupted
cp corners_production.db corners_backup.db
python -c "from data.database import get_db_manager; get_db_manager().create_tables()"
```

### Performance Optimization

#### **Database Optimization**

```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at);
```

#### **Caching Optimization**

```python
# Add Redis for distributed caching (optional)
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
CACHE_DEFAULT_TIMEOUT = 21600  # 6 hours
```

#### **API Optimization**

```python
# Implement request batching
# Use connection pooling
# Implement exponential backoff for retries
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

#### **Load Balancer Configuration**

```nginx
upstream csl_predictions {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://csl_predictions;
    }
}
```

#### **Database Scaling**

For high-volume usage, consider:
- **PostgreSQL**: More robust than SQLite
- **Read Replicas**: Separate read/write operations
- **Connection Pooling**: Manage database connections
- **Caching Layer**: Redis for frequently accessed data

### Vertical Scaling

#### **Resource Monitoring**

```bash
# CPU usage
top -p $(pgrep -f "python app.py")

# Memory usage
ps aux | grep python | awk '{sum+=$4} END {print "Total memory: " sum "%"}'

# Disk I/O
iotop -p $(pgrep -f "python app.py")
```

#### **Performance Tuning**

```python
# Gunicorn worker tuning
workers = (2 * cpu_count()) + 1
worker_class = "gevent"  # For I/O bound applications
worker_connections = 1000
```

---

## 🔄 Continuous Deployment

### GitHub Actions (Example)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy CSL Predictions

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.4
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /home/cslpredictions/corners
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo supervisorctl restart cslpredictions
```

### Deployment Checklist

Before each deployment:

- [ ] **Run Tests**: Ensure all functionality works
- [ ] **Backup Database**: Create pre-deployment backup
- [ ] **Check Dependencies**: Verify all requirements are met
- [ ] **Update Documentation**: Keep docs current
- [ ] **Monitor Logs**: Watch for errors after deployment
- [ ] **Verify Health**: Check all endpoints work correctly
- [ ] **Performance Test**: Ensure response times are acceptable

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks

#### **Daily**
- Check application logs for errors
- Monitor API rate limit usage
- Verify system health endpoint

#### **Weekly**
- Review performance metrics
- Check disk space usage
- Update system packages
- Verify backup integrity

#### **Monthly**
- Review and rotate logs
- Update SSL certificates (if applicable)
- Performance optimization review
- Security update review

### Emergency Procedures

#### **Application Down**

1. **Check Process Status**
   ```bash
   sudo supervisorctl status cslpredictions
   ```

2. **Restart Application**
   ```bash
   sudo supervisorctl restart cslpredictions
   ```

3. **Check Logs**
   ```bash
   tail -f /home/cslpredictions/logs/app.log
   ```

4. **Fallback Plan**
   - Restore from backup if needed
   - Switch to maintenance mode
   - Investigate root cause

#### **Database Corruption**

1. **Stop Application**
2. **Restore from Latest Backup**
3. **Verify Data Integrity**
4. **Restart Application**
5. **Monitor for Issues**

---

This comprehensive deployment guide ensures your CSL Corner Prediction System runs reliably in production with proper monitoring, security, and maintenance procedures.

*Keep this guide updated as your deployment evolves!*
