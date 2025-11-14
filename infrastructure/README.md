# Santé Medical Platform - Kubernetes Deployment

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Ingress (NGINX/Traefik)                      │
│              SSL/TLS Termination + Load Balancing                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼────────┐
│   Frontend     │         │    Backend API   │
│   (Svelte)     │         │    (FastAPI)     │
│   Replicas: 3  │         │   Replicas: 3    │
└────────────────┘         └────────┬─────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼─────┐  ┌─────▼──────┐  ┌────▼──────┐
            │ PostgreSQL  │  │   Redis    │  │  Mailpit  │
            │ StatefulSet │  │ Deployment │  │    Dev    │
            │ PVC Storage │  │            │  └───────────┘
            └─────────────┘  └────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.x (optional, for cert-manager)
- Domain name configured

### 1. Create Namespace
```bash
kubectl create namespace sante-medical
kubectl config set-context --current --namespace=sante-medical
```

### 2. Setup Secrets
```bash
# Generate secrets
./scripts/generate-secrets.sh

# Apply secrets
kubectl apply -f k8s/secrets/
```

### 3. Deploy Infrastructure
```bash
# PostgreSQL + Redis + Storage
kubectl apply -f k8s/infrastructure/

# Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

### 4. Deploy Application
```bash
# Backend
kubectl apply -f k8s/backend/

# Frontend
kubectl apply -f k8s/frontend/

# Ingress
kubectl apply -f k8s/ingress/
```

### 5. Verify Deployment
```bash
kubectl get pods
kubectl get svc
kubectl get ingress
```

## 📁 Directory Structure

```
infrastructure/
├── k8s/
│   ├── namespace.yaml
│   ├── configmaps/
│   │   ├── backend-config.yaml
│   │   └── nginx-config.yaml
│   ├── secrets/
│   │   ├── postgres-secret.yaml
│   │   ├── redis-secret.yaml
│   │   ├── backend-secret.yaml
│   │   └── tls-secret.yaml
│   ├── infrastructure/
│   │   ├── postgres-statefulset.yaml
│   │   ├── postgres-service.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── redis-service.yaml
│   │   └── persistent-volumes.yaml
│   ├── backend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── migration-job.yaml
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── ingress/
│   │   ├── ingress.yaml
│   │   └── cert-manager.yaml
│   └── monitoring/
│       ├── prometheus.yaml
│       ├── grafana.yaml
│       └── alerts.yaml
├── docker/
│   ├── backend/
│   │   ├── Dockerfile.prod
│   │   └── entrypoint.sh
│   └── frontend/
│       ├── Dockerfile.prod
│       └── nginx.conf
├── helm/
│   └── sante-medical/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
└── scripts/
    ├── deploy.sh
    ├── rollback.sh
    ├── generate-secrets.sh
    └── backup-db.sh
```

## 🔧 Configuration

### Environment Variables
Edit `k8s/configmaps/backend-config.yaml` for application settings.

### Secrets Management
Secrets are managed via Kubernetes Secrets. For production, consider using:
- **Sealed Secrets** (Bitnami)
- **External Secrets Operator**
- **HashiCorp Vault**

### SSL/TLS
- Development: Self-signed certificates
- Production: Let's Encrypt via cert-manager

## 📊 Monitoring

### Prometheus Metrics
```bash
kubectl port-forward svc/prometheus 9090:9090
# Open http://localhost:9090
```

### Grafana Dashboards
```bash
kubectl port-forward svc/grafana 3000:3000
# Open http://localhost:3000
# Default: admin/admin
```

## 🔄 CI/CD Integration

### GitLab CI
```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  script:
    - kubectl apply -f k8s/
  only:
    - main
```

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
- name: Deploy to K8s
  run: kubectl apply -f k8s/
```

## 🛡️ Security

### Network Policies
```bash
kubectl apply -f k8s/network-policies/
```

### Pod Security Policies
- Non-root user
- Read-only root filesystem
- No privilege escalation

### RBAC
```bash
kubectl apply -f k8s/rbac/
```

## 💾 Backup & Restore

### Database Backup
```bash
./scripts/backup-db.sh
```

### Restore
```bash
./scripts/restore-db.sh backup-2025-11-14.sql
```

## 🔍 Troubleshooting

### Check Pod Logs
```bash
kubectl logs -f deployment/backend
kubectl logs -f deployment/frontend
```

### Debug Pod
```bash
kubectl exec -it deployment/backend -- /bin/bash
```

### Check Events
```bash
kubectl get events --sort-by='.lastTimestamp'
```

## 📈 Scaling

### Manual Scaling
```bash
kubectl scale deployment backend --replicas=5
kubectl scale deployment frontend --replicas=5
```

### Auto-scaling (HPA)
Already configured via `hpa.yaml` files.

## 🌍 Multi-Region Setup

For high availability:
1. Deploy to multiple clusters
2. Use Global Load Balancer (Cloud provider)
3. Configure cross-region database replication
4. Implement geo-routing

## 📝 License

See LICENSE file.

## 🤝 Contributing

See CONTRIBUTING.md
