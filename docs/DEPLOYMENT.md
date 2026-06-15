# ArrowEra Trade - Deployment Guide

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose 2.20+
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)
- 16GB RAM minimum (32GB recommended)
- 50GB free disk space

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/arrowera-trade.git
cd arrowera-trade

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - OPENAI_API_KEY (or other LLM provider)

# Start all services with Docker Compose
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f

# Run database migrations
docker-compose exec backend python -m backend.db.migrate

# Access services:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3001 (admin/admin)
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
# - Flower (Celery): http://localhost:5555
```

### Manual Installation (Without Docker)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/arrowera_trade"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY=$(openssl rand -hex 32)

# Run migrations
python -m backend.db.migrate

# Start the server
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd apps/web

# Install dependencies
npm install

# Create .env.local
cat > .env.local << EOL
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOL

# Start development server
npm run dev
```

## Production Deployment

### Kubernetes Deployment

```bash
# Navigate to Kubernetes configs
cd infrastructure/k8s

# Create namespace
kubectl create namespace arrowera-trade

# Apply secrets (create from .env)
kubectl create secret generic arrowera-secrets \
  --from-env-file=.env.production \
  -n arrowera-trade

# Apply configurations
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-statefulset.yaml
kubectl apply -f kafka-statefulset.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f worker-deployment.yaml
kubectl apply -f monitoring/

# Check deployment status
kubectl get pods -n arrowera-trade
kubectl get svc -n arrowera-trade
```

### Environment Variables for Production

Create `.env.production` with:

```bash
# Required
ENVIRONMENT=production
SECRET_KEY=<secure-random-key>
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/arrowera
REDIS_URL=redis://prod-redis:6379/0
OPENAI_API_KEY=sk-...

# Security
DEBUG=false
ALLOWED_HOSTS=api.arrowera.trade,dashboard.arrowera.trade
CORS_ORIGINS=https://dashboard.arrowera.trade

# Scale settings
WORKERS=8
DATABASE_POOL_SIZE=50
```

### SSL/TLS Configuration

For production, configure HTTPS:

```yaml
# infrastructure/k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arrowera-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.arrowera.trade
    - dashboard.arrowera.trade
    secretName: arrowera-tls
  rules:
  - host: api.arrowera.trade
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
  - host: dashboard.arrowera.trade
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

## Monitoring Setup

### Prometheus Configuration

Prometheus is pre-configured to scrape:
- Backend API metrics (/metrics)
- Node exporter metrics
- Redis metrics
- PostgreSQL metrics

Access Prometheus at: http://localhost:9090

### Grafana Dashboards

Pre-configured dashboards:
- System Overview
- API Performance
- Agent Metrics
- Database Health
- Cache Performance

Access Grafana at: http://localhost:3001 (admin/admin)

### Alerting Rules

Configure alerts in `monitoring/prometheus/rules.yml`:

```yaml
groups:
- name: arrowera-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: High API latency detected
```

## Backup and Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres arrowera_trade > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20240101.sql | docker-compose exec -T postgres psql -U postgres arrowera_trade
```

### Automated Backups

Use cron jobs or Kubernetes CronJobs:

```yaml
# infrastructure/k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16
            command:
            - /bin/sh
            - -c
            - pg_dump -h postgres -U postgres arrowera_trade | gzip > /backups/backup_$(date +%Y%m%d).sql.gz
            volumeMounts:
            - name: backups
              mountPath: /backups
          volumes:
          - name: backups
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend replicas
kubectl scale deployment backend --replicas=5 -n arrowera-trade

# Scale worker replicas
kubectl scale deployment worker --replicas=10 -n arrowera-trade
```

### Vertical Scaling

Adjust resource limits in deployment YAMLs:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   docker-compose logs postgres
   docker-compose exec postgres pg_isready
   ```

2. **Redis Connection Failed**
   ```bash
   docker-compose logs redis
   docker-compose exec redis redis-cli ping
   ```

3. **Backend Not Starting**
   ```bash
   docker-compose logs backend
   docker-compose exec backend python -c "import backend; print('OK')"
   ```

4. **High Memory Usage**
   - Check for memory leaks in custom agents
   - Reduce DATABASE_POOL_SIZE
   - Scale horizontally instead of vertically

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# With timestamps
docker-compose logs -ft backend
```

## Security Best Practices

1. **Never commit secrets** - Use environment variables or secret management
2. **Enable HTTPS** - Always use TLS in production
3. **Restrict CORS** - Only allow trusted origins
4. **Rotate API keys** - Regularly rotate all API keys
5. **Monitor access** - Review audit logs regularly
6. **Update dependencies** - Keep all packages updated
7. **Use network policies** - Restrict pod-to-pod communication in K8s
8. **Enable authentication** - Don't expose unprotected APIs

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/arrowera-trade/issues
- Documentation: https://docs.arrowera.trade
- Email: support@arrowera.trade
