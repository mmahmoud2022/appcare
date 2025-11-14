#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="sante-medical"

if [ -z "$1" ]; then
    echo -e "${RED}❌ Usage: $0 <backup-file.sql.gz>${NC}"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/sante_db_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will RESTORE the database from backup!${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure? (type 'yes' to continue): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo ""
echo -e "${GREEN}🔄 Restoring PostgreSQL database${NC}"

# Get postgres pod name
POSTGRES_POD=$(kubectl get pod -n $NAMESPACE -l app=postgres -o jsonpath="{.items[0].metadata.name}")

if [ -z "$POSTGRES_POD" ]; then
    echo -e "${RED}❌ PostgreSQL pod not found${NC}"
    exit 1
fi

# Get database credentials
POSTGRES_USER=$(kubectl get secret postgres-secret -n $NAMESPACE -o jsonpath="{.data.POSTGRES_USER}" | base64 -d)
POSTGRES_DB=$(kubectl get secret postgres-secret -n $NAMESPACE -o jsonpath="{.data.POSTGRES_DB}" | base64 -d)

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${YELLOW}📦 Decompressing backup...${NC}"
    gunzip -c "$BACKUP_FILE" > /tmp/restore.sql
    RESTORE_FILE="/tmp/restore.sql"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Scale down backend to prevent connections
echo -e "${YELLOW}⏸️  Scaling down backend...${NC}"
kubectl scale deployment backend -n $NAMESPACE --replicas=0
kubectl wait --for=delete pod -l app=backend -n $NAMESPACE --timeout=60s || true

# Drop existing connections
echo -e "${YELLOW}🔌 Terminating database connections...${NC}"
kubectl exec -n $NAMESPACE $POSTGRES_POD -- psql -U $POSTGRES_USER -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" || true

# Drop and recreate database
echo -e "${YELLOW}🗑️  Dropping existing database...${NC}"
kubectl exec -n $NAMESPACE $POSTGRES_POD -- psql -U $POSTGRES_USER -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
kubectl exec -n $NAMESPACE $POSTGRES_POD -- psql -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_DB;"

# Restore backup
echo -e "${YELLOW}⏳ Restoring backup...${NC}"
cat "$RESTORE_FILE" | kubectl exec -i -n $NAMESPACE $POSTGRES_POD -- psql -U $POSTGRES_USER -d $POSTGRES_DB

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Restore completed successfully!${NC}"
    
    # Scale backend back up
    echo -e "${YELLOW}▶️  Scaling backend back up...${NC}"
    kubectl scale deployment backend -n $NAMESPACE --replicas=3
    kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=180s
    
    echo -e "${GREEN}✅ Backend restored${NC}"
    
    # Cleanup
    rm -f /tmp/restore.sql
else
    echo -e "${RED}❌ Restore failed${NC}"
    
    # Still scale backend back up
    kubectl scale deployment backend -n $NAMESPACE --replicas=3
    exit 1
fi
