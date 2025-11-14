#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="sante-medical"

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <revision_number>${NC}"
    echo ""
    echo "Available rollout history:"
    kubectl rollout history deployment/backend -n $NAMESPACE
    exit 1
fi

REVISION="$1"

echo -e "${YELLOW}🔄 Rolling back to revision $REVISION${NC}"
echo ""

# Rollback backend
echo -e "${YELLOW}⏮️  Rolling back backend deployment...${NC}"
kubectl rollout undo deployment/backend -n $NAMESPACE --to-revision=$REVISION

# Wait for rollback
echo -e "${YELLOW}⏳ Waiting for backend rollback...${NC}"
kubectl rollout status deployment/backend -n $NAMESPACE

echo ""
echo -e "${GREEN}✅ Backend rollback complete!${NC}"
echo ""

# Ask about frontend rollback
read -p "Rollback frontend as well? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏮️  Rolling back frontend deployment...${NC}"
    kubectl rollout undo deployment/frontend -n $NAMESPACE --to-revision=$REVISION
    
    echo -e "${YELLOW}⏳ Waiting for frontend rollback...${NC}"
    kubectl rollout status deployment/frontend -n $NAMESPACE
    
    echo ""
    echo -e "${GREEN}✅ Frontend rollback complete!${NC}"
fi

echo ""
echo "📊 Current status:"
kubectl get pods -n $NAMESPACE
