#!/bin/sh
set -e

# Generate self-signed cert if not present
if [ ! -f /etc/postfix/certs/smtp.crt ]; then
  echo "Generating self-signed TLS certificate..."
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/postfix/certs/smtp.key \
    -out /etc/postfix/certs/smtp.crt \
    -subj "/C=FR/ST=France/L=Paris/O=Sante/OU=IT/CN=sante-app.com"
  chmod 600 /etc/postfix/certs/smtp.key
fi

# Start postfix
postfix start-fg
