#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="sante-medical"
DOCKER_REGISTRY="ghcr.io/your-org"  # CHANGE_ME
VERSION="${1:-latest}"

echo -e "${GREEN}🚀 Deploying Santé Medical to Kubernetes${NC}"
echo "Version: $VERSION"
echo "Namespace: $NAMESPACE"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
kubectl cluster-info | head -1
echo ""

# Create namespace if it doesn't exist
echo -e "${YELLOW}📦 Creating namespace...${NC}"
kubectl apply -f infrastructure/k8s/namespace.yaml

# Apply ConfigMaps
echo -e "${YELLOW}⚙️  Applying ConfigMaps...${NC}"
kubectl apply -f infrastructure/k8s/configmaps/

# Apply Secrets (should be created manually with real values first)
echo -e "${YELLOW}🔐 Checking Secrets...${NC}"
if ! kubectl get secret postgres-secret -n $NAMESPACE &> /dev/null; then
    echo -e "${RED}⚠️  WARNING: postgres-secret not found!${NC}"
    echo "Please create secrets manually or run: ./infrastructure/scripts/generate-secrets.sh"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if ! kubectl get secret backend-secret -n $NAMESPACE &> /dev/null; then
    echo -e "${RED}⚠️  WARNING: backend-secret not found!${NC}"
    echo "Please create secrets manually or run: ./infrastructure/scripts/generate-secrets.sh"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Apply PersistentVolumeClaims
echo -e "${YELLOW}💾 Creating Persistent Volumes...${NC}"
kubectl apply -f infrastructure/k8s/infrastructure/persistent-volumes.yaml

# Deploy PostgreSQL
echo -e "${YELLOW}🐘 Deploying PostgreSQL...${NC}"
kubectl apply -f infrastructure/k8s/infrastructure/postgres-statefulset.yaml
kubectl apply -f infrastructure/k8s/infrastructure/postgres-service.yaml

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}⏳ Waiting for PostgreSQL...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s

# Deploy Redis
echo -e "${YELLOW}📮 Deploying Redis...${NC}"
kubectl apply -f infrastructure/k8s/infrastructure/redis-deployment.yaml
kubectl apply -f infrastructure/k8s/infrastructure/redis-service.yaml

# Wait for Redis to be ready
echo -e "${YELLOW}⏳ Waiting for Redis...${NC}"
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=120s

# Deploy Backend
echo -e "${YELLOW}🔧 Deploying Backend...${NC}"
kubectl apply -f infrastructure/k8s/backend/deployment.yaml
kubectl apply -f infrastructure/k8s/backend/service.yaml

# Wait for Backend to be ready
echo -e "${YELLOW}⏳ Waiting for Backend...${NC}"
kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=300s

# Deploy Backend CronJobs
echo -e "${YELLOW}⏰ Deploying Backend CronJobs...${NC}"
kubectl apply -f infrastructure/k8s/backend/cronjob-update-stats.yaml

# Run initial statistics update job
echo -e "${YELLOW}📊 Running initial statistics update...${NC}"
kubectl apply -f infrastructure/k8s/backend/job-update-stats-init.yaml
echo -e "${GREEN}ℹ️  Initial statistics update job started. Check progress with:${NC}"
echo "   kubectl logs -n $NAMESPACE -l job=update-doctor-statistics-init -f"

# Deploy Frontend
echo -e "${YELLOW}🎨 Deploying Frontend...${NC}"
kubectl apply -f infrastructure/k8s/frontend/deployment.yaml
kubectl apply -f infrastructure/k8s/frontend/service.yaml

# Wait for Frontend to be ready
echo -e "${YELLOW}⏳ Waiting for Frontend...${NC}"
kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=180s

# Apply HPA (Horizontal Pod Autoscaler)
echo -e "${YELLOW}📊 Configuring Autoscaling...${NC}"
kubectl apply -f infrastructure/k8s/backend/hpa.yaml
kubectl apply -f infrastructure/k8s/frontend/hpa.yaml

# Apply Ingress (if cert-manager is installed)
if kubectl get crd clusterissuers.cert-manager.io &> /dev/null; then
    echo -e "${YELLOW}🌐 Configuring Ingress with TLS...${NC}"
    kubectl apply -f infrastructure/k8s/ingress/cert-manager-issuer.yaml
    kubectl apply -f infrastructure/k8s/ingress/ingress.yaml
else
    echo -e "${YELLOW}⚠️  cert-manager not found. Skipping Ingress setup.${NC}"
    echo "Install cert-manager first: kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml"
fi

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Cluster status:"
kubectl get pods -n $NAMESPACE
echo ""
echo "🔍 To check application logs:"
echo "  kubectl logs -f deployment/backend -n $NAMESPACE"
echo "  kubectl logs -f deployment/frontend -n $NAMESPACE"
echo ""
echo "🌐 To access the application:"
echo "  kubectl port-forward -n $NAMESPACE svc/frontend-service 8080:80"
echo "  Then open: http://localhost:8080"
echo ""
echo "📈 To monitor:"
echo "  kubectl top pods -n $NAMESPACE"
echo "  kubectl get hpa -n $NAMESPACE"
