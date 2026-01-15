"""
Email Service - Send emails using Resend API.
"""

import resend
from django.conf import settings
from django.template.loader import render_to_string
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend."""
    
    @classmethod
    def _get_client(cls):
        """Initialize Resend with API key."""
        resend.api_key = settings.RESEND_API_KEY
        return resend
    
    @classmethod
    def send_email(
        cls,
        to: List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        text_content: Optional[str] = None
    ) -> dict:
        """
        Send an email using Resend.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            html_content: HTML body of the email
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            text_content: Plain text version (optional)
        
        Returns:
            dict with 'success' and 'id' or 'error'
        """
        client = cls._get_client()
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        try:
            params = {
                "from": from_email,
                "to": to,
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            response = client.Emails.send(params)
            logger.info(f"Email sent successfully to {to}: {response}")
            return {"success": True, "id": response.get("id")}
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def send_verification_email(cls, user, verification_url: str) -> dict:
        """Send email verification email."""
        subject = "Verify Your Email - Job Application Tracker"
        
        html_content = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
            'app_name': 'Job Application Tracker'
        })
        
        text_content = f"""
Hi {user.first_name or user.username},

Welcome to Job Application Tracker! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Best regards,
The Job Application Tracker Team
        """
        
        return cls.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    @classmethod
    def send_password_reset_email(cls, user, reset_url: str) -> dict:
        """Send password reset email."""
        subject = "Reset Your Password - Job Application Tracker"
        
        html_content = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'app_name': 'Job Application Tracker'
        })
        
        text_content = f"""
Hi {user.first_name or user.username},

You requested to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email. Your password will remain unchanged.

Best regards,
The Job Application Tracker Team
        """
        
        return cls.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    @classmethod
    def send_welcome_email(cls, user) -> dict:
        """Send welcome email after verification."""
        subject = "Welcome to Job Application Tracker! 🎉"
        
        html_content = render_to_string('emails/welcome.html', {
            'user': user,
            'app_name': 'Job Application Tracker'
        })
        
        text_content = f"""
Hi {user.first_name or user.username},

Your email has been verified! Welcome to Job Application Tracker.

You can now:
- Track all your job applications in one place
- Schedule and prepare for interviews
- Generate AI-powered cover letters
- Analyze job match scores
- Get personalized interview questions

Start tracking your job search journey today!

Best regards,
The Job Application Tracker Team
        """
        
        return cls.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    @classmethod
    def send_password_changed_email(cls, user) -> dict:
        """Send confirmation that password was changed."""
        subject = "Password Changed Successfully - Job Application Tracker"
        
        html_content = render_to_string('emails/password_changed.html', {
            'user': user,
            'app_name': 'Job Application Tracker'
        })
        
        text_content = f"""
Hi {user.first_name or user.username},

Your password has been successfully changed.

If you did not make this change, please contact support immediately.

Best regards,
The Job Application Tracker Team
        """
        
        return cls.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
