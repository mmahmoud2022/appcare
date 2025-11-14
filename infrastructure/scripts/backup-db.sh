#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="sante-medical"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}💾 Backing up PostgreSQL database${NC}"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get postgres pod name
POSTGRES_POD=$(kubectl get pod -n $NAMESPACE -l app=postgres -o jsonpath="{.items[0].metadata.name}")

if [ -z "$POSTGRES_POD" ]; then
    echo -e "${RED}❌ PostgreSQL pod not found${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Found PostgreSQL pod: $POSTGRES_POD${NC}"

# Get database credentials
POSTGRES_USER=$(kubectl get secret postgres-secret -n $NAMESPACE -o jsonpath="{.data.POSTGRES_USER}" | base64 -d)
POSTGRES_DB=$(kubectl get secret postgres-secret -n $NAMESPACE -o jsonpath="{.data.POSTGRES_DB}" | base64 -d)

BACKUP_FILE="$BACKUP_DIR/sante_db_${TIMESTAMP}.sql"

echo -e "${YELLOW}⏳ Creating database backup...${NC}"

# Create backup
kubectl exec -n $NAMESPACE $POSTGRES_POD -- pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    # Compress backup
    echo -e "${YELLOW}📦 Compressing backup...${NC}"
    gzip "$BACKUP_FILE"
    
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    
    echo -e "${GREEN}✅ Backup completed successfully!${NC}"
    echo ""
    echo "Backup file: ${BACKUP_FILE}.gz"
    echo "Size: $BACKUP_SIZE"
    echo ""
    
    # Keep only last 7 backups
    echo -e "${YELLOW}🧹 Cleaning old backups (keeping last 7)...${NC}"
    ls -t $BACKUP_DIR/sante_db_*.sql.gz | tail -n +8 | xargs -r rm
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    echo ""
    echo "Available backups:"
    ls -lh $BACKUP_DIR/sante_db_*.sql.gz
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi
