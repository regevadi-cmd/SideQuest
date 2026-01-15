"""Email notification service using Resend."""
import os
import logging
from typing import Optional
from datetime import datetime

from data.models import Job, Notification

logger = logging.getLogger(__name__)

# Check if resend is available
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("resend package not installed. Email notifications disabled.")


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        """Initialize the email service."""
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("NOTIFICATION_EMAIL_FROM", "SideQuest <notifications@resend.dev>")
        self.enabled = RESEND_AVAILABLE and bool(self.api_key)

        if self.enabled:
            resend.api_key = self.api_key

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return self.enabled

    def send_job_alert(self, to_email: str, jobs: list[Job], search_query: str = "") -> bool:
        """Send an email alert about new job matches.

        Args:
            to_email: Recipient email address
            jobs: List of new jobs to include
            search_query: Optional search query for context

        Returns:
            True if email was sent successfully
        """
        if not self.enabled:
            logger.warning("Email service not configured")
            return False

        if not jobs:
            return False

        # Build job list HTML
        job_items = []
        for job in jobs[:10]:  # Limit to 10 jobs per email
            salary_str = f" - {job.salary_text}" if job.salary_text else ""
            job_items.append(f"""
            <tr>
                <td style="padding: 16px; border-bottom: 1px solid #E2E8F0;">
                    <div style="font-family: 'Plus Jakarta Sans', system-ui, sans-serif; font-weight: 600; color: #0F172A; font-size: 16px;">
                        {job.title}
                    </div>
                    <div style="color: #0891B2; font-size: 14px; margin-top: 4px;">
                        {job.company}
                    </div>
                    <div style="color: #64748B; font-size: 13px; margin-top: 4px;">
                        {job.location}{salary_str}
                    </div>
                    <a href="{job.url}" style="display: inline-block; margin-top: 12px; padding: 8px 16px; background: #0891B2; color: white; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600;">
                        View Job
                    </a>
                </td>
            </tr>
            """)

        jobs_html = "".join(job_items)
        remaining = len(jobs) - 10 if len(jobs) > 10 else 0
        remaining_text = f"<p style='color: #64748B; text-align: center; margin-top: 16px;'>+ {remaining} more jobs</p>" if remaining else ""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: system-ui, -apple-system, sans-serif; background: #F1F5F9; padding: 24px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%); padding: 32px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 700;">
                        New Job Matches!
                    </h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">
                        {len(jobs)} new job{'s' if len(jobs) > 1 else ''} found for your search
                    </p>
                </div>

                <!-- Jobs List -->
                <table style="width: 100%; border-collapse: collapse;">
                    {jobs_html}
                </table>
                {remaining_text}

                <!-- Footer -->
                <div style="padding: 24px; background: #F8FAFC; text-align: center;">
                    <p style="color: #64748B; font-size: 12px; margin: 0;">
                        You're receiving this because you have email notifications enabled in SideQuest.
                    </p>
                    <p style="color: #94A3B8; font-size: 11px; margin: 8px 0 0 0;">
                        To change your notification preferences, visit the Settings page.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"SideQuest: {len(jobs)} New Job{'s' if len(jobs) > 1 else ''} Found!",
                "html": html_content
            }

            resend.Emails.send(params)
            logger.info(f"Job alert email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send job alert email: {e}")
            return False

    def send_daily_digest(self, to_email: str, summary: dict) -> bool:
        """Send a daily digest email with application and search summary.

        Args:
            to_email: Recipient email address
            summary: Dict with keys: new_jobs, applications_updated, upcoming_deadlines

        Returns:
            True if email was sent successfully
        """
        if not self.enabled:
            return False

        new_jobs = summary.get("new_jobs", 0)
        apps_updated = summary.get("applications_updated", 0)
        deadlines = summary.get("upcoming_deadlines", [])

        # Build deadlines HTML
        deadline_items = []
        for d in deadlines[:5]:
            deadline_items.append(f"""
            <div style="padding: 12px; background: #FEF3C7; border-radius: 8px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: #92400E;">{d.get('job_title', 'Job')}</div>
                <div style="color: #B45309; font-size: 13px;">{d.get('next_step', 'Action needed')} - {d.get('date', 'Soon')}</div>
            </div>
            """)
        deadlines_html = "".join(deadline_items) if deadline_items else "<p style='color: #64748B;'>No upcoming deadlines</p>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: system-ui, -apple-system, sans-serif; background: #F1F5F9; padding: 24px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%); padding: 32px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 700;">
                        Your Daily Digest
                    </h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">
                        {datetime.now().strftime('%B %d, %Y')}
                    </p>
                </div>

                <!-- Stats -->
                <div style="display: flex; padding: 24px;">
                    <div style="flex: 1; text-align: center; padding: 16px;">
                        <div style="font-size: 32px; font-weight: 700; color: #0891B2;">{new_jobs}</div>
                        <div style="font-size: 13px; color: #64748B; text-transform: uppercase;">New Jobs</div>
                    </div>
                    <div style="flex: 1; text-align: center; padding: 16px; border-left: 1px solid #E2E8F0;">
                        <div style="font-size: 32px; font-weight: 700; color: #10B981;">{apps_updated}</div>
                        <div style="font-size: 13px; color: #64748B; text-transform: uppercase;">Apps Updated</div>
                    </div>
                </div>

                <!-- Deadlines -->
                <div style="padding: 24px; border-top: 1px solid #E2E8F0;">
                    <h2 style="font-size: 16px; color: #0F172A; margin: 0 0 16px 0;">Upcoming Deadlines</h2>
                    {deadlines_html}
                </div>

                <!-- Footer -->
                <div style="padding: 24px; background: #F8FAFC; text-align: center;">
                    <a href="#" style="display: inline-block; padding: 12px 24px; background: #0891B2; color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">
                        Open SideQuest
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"SideQuest Daily Digest - {datetime.now().strftime('%B %d')}",
                "html": html_content
            }

            resend.Emails.send(params)
            logger.info(f"Daily digest sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send daily digest: {e}")
            return False

    def send_notification_email(self, to_email: str, notification: Notification) -> bool:
        """Send an email for a specific notification.

        Args:
            to_email: Recipient email address
            notification: The notification to send

        Returns:
            True if email was sent successfully
        """
        if not self.enabled:
            return False

        # Determine icon and color based on type
        type_config = {
            "new_jobs": {"icon": "", "color": "#0891B2", "bg": "rgba(8, 145, 178, 0.1)"},
            "application_update": {"icon": "", "color": "#10B981", "bg": "rgba(16, 185, 129, 0.1)"},
            "system": {"icon": "", "color": "#F59E0B", "bg": "rgba(245, 158, 11, 0.1)"}
        }
        config = type_config.get(notification.type, type_config["system"])

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: system-ui, -apple-system, sans-serif; background: #F1F5F9; padding: 24px;">
            <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="padding: 32px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 16px;">{config['icon']}</div>
                    <h1 style="color: #0F172A; font-size: 20px; font-weight: 700; margin: 0 0 8px 0;">
                        {notification.title}
                    </h1>
                    <p style="color: #64748B; font-size: 15px; margin: 0; line-height: 1.5;">
                        {notification.message}
                    </p>
                </div>
                <div style="padding: 24px; background: #F8FAFC; text-align: center;">
                    <p style="color: #94A3B8; font-size: 11px; margin: 0;">
                        SideQuest Job Search Agent
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"SideQuest: {notification.title}",
                "html": html_content
            }

            resend.Emails.send(params)
            return True

        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_job_alert_email(to_email: str, jobs: list[Job]) -> bool:
    """Convenience function to send job alert email."""
    service = get_email_service()
    return service.send_job_alert(to_email, jobs)
