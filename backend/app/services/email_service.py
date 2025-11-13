"""
Email Service with SMTP (Mailpit/Postfix) and Amazon SES support
Handles sending emails with templates, retry logic, delivery tracking, and automatic fallback
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import asyncio
from pathlib import Path
import mimetypes
from enum import Enum

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class EmailProvider(str, Enum):
    """Available email providers"""
    SES = "ses"
    SMTP = "smtp"


class EmailService:
    """
    Email service for sending emails via SMTP or Amazon SES with automatic fallback
    
    Provider selection:
    - SMTP: For development (Mailpit) or production (Postfix)
    - Amazon SES: For production with high deliverability
    - Automatic fallback: If primary provider fails, tries backup provider
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        """
        Initialize email service
        
        Args:
            provider: Primary email provider ('smtp' or 'ses')
            from_email: Default sender email address
            from_name: Default sender name
        """
        self.provider = provider or settings.EMAIL_PROVIDER
        self.from_email = from_email or settings.EMAIL_FROM
        self.from_name = from_name or settings.EMAIL_FROM_NAME
        self.logger = logger
        
        # Initialize available providers
        self.available_providers = self._get_available_providers()
        
        # SES client will be lazily initialized
        self.ses_client = None
        
        # Daily limits tracking (optional, for monitoring)
        self.daily_limits = {
            EmailProvider.SES: 50000,  # After verification
            EmailProvider.SMTP: 10000  # Conservative estimate
        }
        self.sent_today = {}
        
        self.logger.info(
            f"Email service initialized with provider: {self.provider}",
            extra={
                "primary_provider": self.provider,
                "available_providers": [p.value for p in self.available_providers],
                "smtp_host": getattr(settings, 'SMTP_HOST', None)
            }
        )
    
    def _get_available_providers(self) -> List[EmailProvider]:
        """
        Get list of available providers based on configuration
        Returns providers in priority order
        """
        providers = []
        
        # Primary provider first
        if self.provider == "ses" and self._is_ses_configured():
            providers.append(EmailProvider.SES)
        elif self.provider == "smtp" and self._is_smtp_configured():
            providers.append(EmailProvider.SMTP)
        
        # Add backup providers
        if self.provider != "ses" and self._is_ses_configured():
            providers.append(EmailProvider.SES)
        if self.provider != "smtp" and self._is_smtp_configured():
            providers.append(EmailProvider.SMTP)
        
        return providers
    
    def _is_ses_configured(self) -> bool:
        """Check if SES is properly configured"""
        return bool(
            getattr(settings, 'AWS_SES_ACCESS_KEY_ID', None) and
            getattr(settings, 'AWS_SES_SECRET_ACCESS_KEY', None) and
            getattr(settings, 'AWS_SES_REGION', None)
        )
    
    def _is_smtp_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(getattr(settings, 'SMTP_HOST', None))
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email with automatic fallback to backup provider if primary fails
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Plain text email body (optional)
            from_email: Sender email (optional, uses default if not provided)
            from_name: Sender name (optional)
            attachments: List of attachments (optional)
            metadata: Custom metadata for tracking (optional)
            reply_to: Reply-to email address (optional)
            
        Returns:
            Dictionary with send result
        """
        from_email = from_email or self.from_email
        from_name = from_name or self.from_name
        
        if not settings.EMAIL_ENABLED:
            self.logger.warning("Email sending is disabled")
            return {
                "success": False,
                "error": "Email sending is disabled",
                "to_email": to_email
            }
        
        if not self.available_providers:
            self.logger.error("No email providers configured")
            return {
                "success": False,
                "error": "No email providers configured",
                "to_email": to_email
            }
        
        last_error = None
        attempted_providers = []
        
        # Try each available provider
        for provider in self.available_providers:
            attempted_providers.append(provider.value)
            
            try:
                self.logger.info(
                    f"Attempting to send email via {provider.value}",
                    extra={"provider": provider.value, "to_email": to_email}
                )
                
                if provider == EmailProvider.SES:
                    result = await self._send_via_ses(
                        to_email, subject, html_content, plain_content,
                        from_email, from_name, reply_to, metadata
                    )
                else:  # SMTP
                    result = await self._send_via_smtp(
                        to_email, subject, html_content, plain_content,
                        from_email, from_name, reply_to, attachments
                    )
                
                if result.get("success"):
                    self._increment_counter(provider)
                    self.logger.info(
                        f"Email sent successfully via {provider.value}",
                        extra={
                            "provider": provider.value,
                            "to_email": to_email,
                            "subject": subject,
                            "attempted_providers": attempted_providers
                        }
                    )
                    return result
                else:
                    last_error = result.get("error", "Unknown error")
                    self.logger.warning(
                        f"Provider {provider.value} returned failure",
                        extra={"error": last_error, "provider": provider.value}
                    )
                    
            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    f"Provider {provider.value} failed, trying next provider",
                    extra={
                        "error": str(e),
                        "provider": provider.value,
                        "to_email": to_email
                    }
                )
                continue
        
        # All providers failed
        self.logger.error(
            "All email providers failed",
            extra={
                "to_email": to_email,
                "subject": subject,
                "last_error": last_error,
                "attempted_providers": attempted_providers
            }
        )
        
        return {
            "success": False,
            "error": f"All providers failed. Last error: {last_error}",
            "to_email": to_email,
            "attempted_providers": attempted_providers
        }
    
    def _increment_counter(self, provider: EmailProvider):
        """Increment daily email counter for monitoring"""
        today = datetime.utcnow().date().isoformat()
        key = f"{provider.value}_{today}"
        self.sent_today[key] = self.sent_today.get(key, 0) + 1
    
    async def _send_via_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: Optional[str],
        metadata: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send email via Amazon SES"""
        try:
            # Format sender with name
            sender = f"{from_name} <{from_email}>" if from_name else from_email

            # Prepare email body
            body = {"Html": {"Data": html_content, "Charset": "UTF-8"}}
            if plain_content:
                body["Text"] = {"Data": plain_content, "Charset": "UTF-8"}

            # Prepare send parameters
            send_params = {
                "Source": sender,
                "Destination": {"ToAddresses": [to_email]},
                "Message": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": body
                }
            }

            # Add reply-to if provided
            if reply_to:
                send_params["ReplyToAddresses"] = [reply_to]

            # Add configuration set if configured
            if getattr(settings, 'AWS_SES_CONFIGURATION_SET', None):
                send_params["ConfigurationSetName"] = settings.AWS_SES_CONFIGURATION_SET

            # Add tags from metadata
            if metadata:
                send_params["Tags"] = [
                    {"Name": key, "Value": value}
                    for key, value in metadata.items()
                ]

            # Lazy-initialize boto3 SES client if needed
            if self.ses_client is None:
                try:
                    import boto3
                    self.ses_client = boto3.client(
                        'ses',
                        region_name=settings.AWS_SES_REGION,
                        aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY
                    )
                    self.logger.info("Amazon SES client initialized successfully")
                except ImportError:
                    self.logger.error("boto3 not installed. Install with: pip install boto3")
                    raise

            # boto3 is synchronous; call it in a thread executor
            loop = asyncio.get_running_loop()
            send_func = lambda: self.ses_client.send_email(**send_params)
            response = await loop.run_in_executor(None, send_func)

            message_id = response.get("MessageId") if isinstance(response, dict) else getattr(response, 'MessageId', None)

            return {
                "success": True,
                "message_id": message_id,
                "provider": "ses",
                "to_email": to_email,
                "from_email": from_email,
                "sent_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Amazon SES error: {str(e)}")
            raise

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Send email via SMTP (Mailpit for dev, Postfix for prod)
        """
        try:
            import aiosmtplib
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{from_name} <{from_email}>" if from_name else from_email
            message["To"] = to_email
            
            if reply_to:
                message["Reply-To"] = reply_to
            
            # Add plain text and HTML parts
            if plain_content:
                part1 = MIMEText(plain_content, "plain", "utf-8")
                message.attach(part1)
            
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)
            
            # Add attachments if provided
            if attachments:
                for attachment_data in attachments:
                    filename = attachment_data.get("filename") or "attachment"
                    content = attachment_data.get("content")

                    # If content is a path, read bytes
                    if isinstance(content, (str, Path)) and Path(str(content)).exists():
                        content = Path(str(content)).read_bytes()

                    # If content is a string, encode
                    if isinstance(content, str):
                        content = content.encode("utf-8")

                    if content is None:
                        continue

                    # Guess mime type
                    mimetype, _ = mimetypes.guess_type(filename)
                    if mimetype:
                        maintype, subtype = mimetype.split('/', 1)
                    else:
                        maintype, subtype = 'application', 'octet-stream'

                    part = MIMEBase(maintype, subtype)
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"'
                    )
                    message.attach(part)
            
            # Get TLS settings
            use_tls = getattr(settings, 'SMTP_USE_SSL', False)
            start_tls = getattr(settings, 'SMTP_USE_STARTTLS', False)

            # Fallback to legacy settings if needed
            if use_tls is None:
                use_tls = getattr(settings, 'SMTP_TLS', False)
            if start_tls is None:
                start_tls = getattr(settings, 'SMTP_SSL', False)

            # Get SMTP credentials
            smtp_user = getattr(settings, 'SMTP_USER', None)
            smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
            
            # Only use authentication if both credentials are provided and non-empty
            # Mailpit doesn't need auth, Postfix on localhost usually doesn't either
            use_auth = bool(smtp_user and smtp_password and smtp_user.strip() and smtp_password.strip())
            
            # Send email via SMTP
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=smtp_user if use_auth else None,
                password=smtp_password if use_auth else None,
                use_tls=bool(use_tls),
                start_tls=bool(start_tls),
            )
            
            return {
                "success": True,
                "message_id": f"smtp_{datetime.utcnow().timestamp()}",
                "provider": "smtp",
                "to_email": to_email,
                "from_email": from_email,
                "sent_at": datetime.utcnow().isoformat(),
                "smtp_host": settings.SMTP_HOST,
                "authenticated": use_auth
            }
            
        except Exception as e:
            self.logger.error(f"SMTP error: {str(e)}")
            raise
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get email usage statistics for today"""
        today = datetime.utcnow().date().isoformat()
        stats = {}
        
        for provider in self.available_providers:
            key = f"{provider.value}_{today}"
            sent = self.sent_today.get(key, 0)
            limit = self.daily_limits.get(provider, 0)
            
            stats[provider.value] = {
                "sent_today": sent,
                "daily_limit": limit,
                "remaining": max(0, limit - sent),
                "usage_percent": round((sent / limit * 100), 2) if limit > 0 else 0
            }
        
        return {
            "date": today,
            "providers": stats,
            "total_sent": sum(s["sent_today"] for s in stats.values()),
            "available_providers": [p.value for p in self.available_providers]
        }
    
    # Template methods below remain unchanged
    
    async def send_appointment_confirmation(
        self,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        appointment_type: str,
        cancellation_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send appointment confirmation email"""
        from app.templates.email_templates import EmailTemplates
        
        subject = "Confirmation de rendez-vous - Santé"
        html_content = EmailTemplates.appointment_confirmation(
            patient_name=patient_name,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            appointment_type=appointment_type,
            cancellation_url=cancellation_url or "#"
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            metadata={
                "template": "appointment_confirmation",
                "patient_name": patient_name
            }
        )
    
    async def send_appointment_reminder(
        self,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str
    ) -> Dict[str, Any]:
        """Send appointment reminder email"""
        from app.templates.email_templates import EmailTemplates
        
        subject = "Rappel de rendez-vous - Santé"
        html_content = EmailTemplates.appointment_reminder(
            patient_name=patient_name,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            metadata={
                "template": "appointment_reminder",
                "patient_name": patient_name
            }
        )
    
    async def send_password_reset(
        self,
        to_email: str,
        first_name: str,
        reset_url: str,
        expiry_minutes: int = 15
    ) -> Dict[str, Any]:
        """Send password reset email"""
        from app.templates.email_templates import EmailTemplates
        
        subject = "Réinitialisation de mot de passe - Santé"
        html_content = EmailTemplates.password_reset(
            first_name=first_name,
            reset_url=reset_url,
            expiry_minutes=expiry_minutes
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            metadata={
                "template": "password_reset",
                "user_email": to_email
            }
        )
    
    async def send_prescription_ready(
        self,
        to_email: str,
        patient_name: str,
        medication_name: str,
        pickup_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send prescription ready notification"""
        from app.templates.email_templates import EmailTemplates
        
        subject = "Votre ordonnance est prête - Santé"
        html_content = EmailTemplates.prescription_ready(
            patient_name=patient_name,
            medication_name=medication_name,
            pickup_instructions=pickup_instructions or "Contactez votre pharmacie"
        )
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            metadata={
                "template": "prescription_ready",
                "patient_name": patient_name
            }
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get singleton email service instance
    
    Returns:
        EmailService instance
    """
    global _email_service
    
    if _email_service is None:
        _email_service = EmailService()
    
    return _email_service