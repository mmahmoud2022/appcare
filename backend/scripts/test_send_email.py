"""Simple test script to send an email using the project's EmailService.

Usage:
  # from repo root
  python -m backend.scripts.test_send_email

Environment variables:
  TEST_EMAIL_TO - recipient address (required)
  TEST_EMAIL_FROM - optional override sender

Notes:
  Run this inside the backend container for correct PYTHONPATH and settings, e.g.:
    docker compose exec backend python -m backend.scripts.test_send_email
"""
import os
import asyncio

from app.services.email_service import get_email_service


async def main():
    to_email = os.getenv("TEST_EMAIL_TO")
    if not to_email:
        print("Please set TEST_EMAIL_TO environment variable to a valid email address")
        return

    from_email = os.getenv("TEST_EMAIL_FROM")

    service = get_email_service()

    try:
        result = await service.send_email(
            to_email=to_email,
            subject="Test email from Santé platform",
            html_content="<p>This is a test email sent from the Santé backend.</p>",
            plain_content="This is a test email sent from the Santé backend.",
            from_email=from_email,
        )
        print("Send result:", result)
    except Exception as e:
        print("Error sending email:", str(e))


if __name__ == "__main__":
    asyncio.run(main())
