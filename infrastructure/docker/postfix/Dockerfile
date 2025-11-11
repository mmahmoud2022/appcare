FROM alpine:3.19
LABEL maintainer="Santé Platform"

RUN apk add --no-cache postfix cyrus-sasl cyrus-sasl-plain openssl

# Create postfix user
RUN adduser -D -u 1001 postfixuser

# Create directories for certs and config
RUN mkdir -p /etc/postfix/certs /var/spool/postfix

COPY main.cf /etc/postfix/main.cf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 25

ENTRYPOINT ["/entrypoint.sh"]
