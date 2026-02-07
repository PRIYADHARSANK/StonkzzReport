import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import os
from typing import List, Optional

class EmailNotifier:
    """
    Email notification service for StonkzzReport
    Sends automated emails when data fetching completes
    """
    
    def __init__(self):
        """Initialize email notifier with environment variables"""
        self.sender_email = os.getenv("EMAIL_SENDER", "")
        self.app_password = os.getenv("EMAIL_APP_PASSWORD", "")
        self.recipients = self._parse_recipients(os.getenv("EMAIL_RECIPIENTS", ""))
        self.enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        
    def _parse_recipients(self, recipients_str: str) -> List[str]:
        """Parse comma-separated recipient emails"""
        if not recipients_str:
            return []
        return [email.strip() for email in recipients_str.split(",") if email.strip()]
    
    def send_report_notification(
        self, 
        subject: Optional[str] = None,
        body: Optional[str] = None,
        custom_recipients: Optional[List[str]] = None,
        pdf_path: Optional[str] = None
    ) -> bool:
        """
        Send email notification about completed data fetch
        
        Args:
            subject: Email subject (optional, uses default if not provided)
            body: Email body (optional, uses default if not provided)
            custom_recipients: Override default recipients (optional)
            pdf_path: Path to PDF file to attach (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            print("📧 Email notifications are disabled (EMAIL_ENABLED=false)")
            return False
            
        if not self.sender_email or not self.app_password:
            print("⚠️  Email credentials not configured in .env file")
            return False
            
        recipients = custom_recipients or self.recipients
        if not recipients:
            print("⚠️  No email recipients configured")
            return False
        
        # Default subject and body
        if subject is None:
            subject = "StonkzzReport - Data Fetch Complete"
            
        if body is None:
            body = self._generate_default_body(has_attachment=pdf_path is not None)
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            # Attach PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_attachment = MIMEApplication(pdf_file.read(), _subtype='pdf')
                        pdf_filename = os.path.basename(pdf_path)
                        pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                        msg.attach(pdf_attachment)
                        print(f"📎 Attached PDF: {pdf_filename} ({os.path.getsize(pdf_path) / 1024:.2f} KB)")
                except Exception as e:
                    print(f"⚠️  Warning: Could not attach PDF: {e}")
                    # Continue sending email without attachment
            
            # Send email via Gmail SMTP
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {len(recipients)} recipient(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Recipients: {', '.join(recipients)}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("❌ Email authentication failed. Please check your app password.")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error occurred: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def _generate_default_body(self, has_attachment: bool = False) -> str:
        """Generate default email body"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
        
        attachment_note = ""
        if has_attachment:
            attachment_note = "\n📎 A PDF report is attached to this email for your review.\n"
        
        body = f"""Good day,

This is an automated notification from StonkzzReport.

The scheduled data fetch has completed successfully.{attachment_note}
Fetch Details:
- Timestamp: {timestamp}
- Data Sources: Nifty, VIX, GIFT Nifty, Gold/Silver, Global Markets, Currency, FII/DII, PCR OI
- Status: Complete

The latest market data is now available in your report dashboard.

---
Regards,
StonkzzReport Automation Engine
"""
        return body


def send_email(subject: Optional[str] = None, body: Optional[str] = None) -> bool:
    """
    Convenience function to send email notification
    
    Args:
        subject: Email subject (optional)
        body: Email body (optional)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    notifier = EmailNotifier()
    return notifier.send_report_notification(subject=subject, body=body)


def send_email_with_attachment(subject: Optional[str] = None, body: Optional[str] = None, pdf_path: Optional[str] = None) -> bool:
    """
    Convenience function to send email notification with PDF attachment
    
    Args:
        subject: Email subject (optional)
        body: Email body (optional)
        pdf_path: Path to PDF file to attach (optional)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    notifier = EmailNotifier()
    return notifier.send_report_notification(subject=subject, body=body, pdf_path=pdf_path)


if __name__ == "__main__":
    # Test the email notifier
    print("Testing Email Notifier...")
    print("-" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    # Look for .env in parent directories if not found here
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    
    # Send test email
    success = send_email(
        subject="StonkzzReport - Test Email",
        body="This is a test email from the StonkzzReport email notification system."
    )
    
    if success:
        print("\n✅ Test email sent successfully!")
    else:
        print("\n❌ Failed to send test email. Please check your configuration.")
