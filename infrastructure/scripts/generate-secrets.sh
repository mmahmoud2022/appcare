#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="sante-medical"

echo -e "${YELLOW}🔐 Generating Kubernetes Secrets${NC}"
echo ""

# Generate random secrets
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

generate_jwt_secret() {
    openssl rand -hex 32
}

# Prompt for values
read -p "Enter PostgreSQL password (or press Enter for random): " POSTGRES_PASSWORD
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(generate_secret)}

read -p "Enter JWT secret (or press Enter for random): " JWT_SECRET
JWT_SECRET=${JWT_SECRET:-$(generate_jwt_secret)}

read -p "Enter SMTP password (optional): " SMTP_PASSWORD

read -p "Enter AWS Access Key (optional): " AWS_ACCESS_KEY

read -p "Enter AWS Secret Key (optional): " AWS_SECRET_KEY

echo ""
echo -e "${GREEN}📝 Creating Secrets...${NC}"

# Create postgres-secret
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=sante_user \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=POSTGRES_DB=sante_db \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ postgres-secret created${NC}"

# Build DATABASE_URL
DATABASE_URL="postgresql://sante_user:${POSTGRES_PASSWORD}@postgres-service:5432/sante_db"
REDIS_URL="redis://redis-service:6379/0"

# Create backend-secret
kubectl create secret generic backend-secret \
  --from-literal=SECRET_KEY="$JWT_SECRET" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=REDIS_URL="$REDIS_URL" \
  --from-literal=SMTP_PASSWORD="${SMTP_PASSWORD:-}" \
  --from-literal=AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY:-}" \
  --from-literal=AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY:-}" \
  --from-literal=SENTRY_DSN="" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ backend-secret created${NC}"

echo ""
echo -e "${GREEN}🎉 Secrets generated successfully!${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Save these credentials securely!${NC}"
echo ""
echo "PostgreSQL Password: $POSTGRES_PASSWORD"
echo "JWT Secret: $JWT_SECRET"
echo "Database URL: $DATABASE_URL"
echo ""
echo "To view secrets:"
echo "  kubectl get secrets -n $NAMESPACE"
echo "  kubectl describe secret postgres-secret -n $NAMESPACE"
