FROM alpine:3.19
LABEL maintainer="Santé Platform"

# Installer Postfix et dépendances utiles
RUN apk add --no-cache postfix cyrus-sasl ca-certificates openssl bash tini

# Créer utilisateur dédié non-root (pour bonnes pratiques Docker)
RUN adduser -D -u 1001 postfixuser

# Créer répertoires nécessaires
RUN mkdir -p /etc/postfix/certs /var/spool/postfix /var/log/postfix

# Copier configuration et script d’entrée
COPY main.cf /etc/postfix/main.cf
RUN echo "postmaster: root" > /etc/postfix/aliases && postalias /etc/postfix/aliases
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Fixer droits : root doit posséder les fichiers de config Postfix
RUN chown -R root:root /etc/postfix && chmod -R 755 /etc/postfix

# Exposer port SMTP
EXPOSE 25

# Santé : tini pour un bon signal handling (Docker best practice)
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
