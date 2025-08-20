import boto3
import os
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

class SESEmailService:
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        self.sender_email = os.environ.get('SES_SENDER_EMAIL', 'noreply@alldays.club')
        self.verified_emails = os.environ.get('SES_VERIFIED_EMAILS', '').split(',') if os.environ.get('SES_VERIFIED_EMAILS') else []

    def send_confirmation_email(self, 
                               recipient_email: str, 
                               first_name: str, 
                               last_name: str, 
                               booking_id: str, 
                               selected_sports: str, 
                               event_date: str, 
                               event_location: str, 
                               orangetheory_batch: Optional[str] = None) -> bool:
        """
        Send confirmation email for event registration
        """
        try:
            # Create email content
            subject = f"Registration Confirmed - Alldays Event (Booking ID: {booking_id})"
            
            # Parse selected sports for better display
            sports_list = []
            try:
                import json
                sports_data = json.loads(selected_sports)
                if isinstance(sports_data, list):
                    sports_list = sports_data
                else:
                    sports_list = [selected_sports]
            except:
                sports_list = [selected_sports]
            
            # Format sports for display
            sports_display = ", ".join([sport.title() for sport in sports_list])
            
            # Create HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Registration Confirmation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #6b58cd 0%, #e7ff00 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .booking-id {{ background: #e7ff00; color: #333; padding: 10px; border-radius: 5px; font-weight: bold; text-align: center; margin: 20px 0; }}
                    .details {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 5px 0; border-bottom: 1px solid #eee; }}
                    .detail-label {{ font-weight: bold; color: #6b58cd; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Registration Confirmed!</h1>
                        <p>Welcome to Alldays x OnTour</p>
                    </div>
                    
                    <div class="content">
                        <p>Hi {first_name.title()} {last_name.title()},</p>
                        
                        <p>Your registration for the Alldays event has been successfully confirmed! Here are your registration details:</p>
                        
                        <div class="booking-id">
                            Booking ID: {booking_id}
                        </div>
                        
                        <div class="details">
                            <div class="detail-row">
                                <span class="detail-label">Name:</span>
                                <span>{first_name.title()} {last_name.title()}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Email:</span>
                                <span>{recipient_email}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Selected Sports:</span>
                                <span>{sports_display}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Event Date:</span>
                                <span>{event_date}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Event Location:</span>
                                <span>{event_location}</span>
                            </div>
                            {f'<div class="detail-row"><span class="detail-label">Orangetheory Batch:</span><span>{orangetheory_batch.title()}</span></div>' if orangetheory_batch else ''}
                        </div>
                        
                        <h3>What's Next?</h3>
                        <ul>
                            <li>Please arrive 15 minutes before your scheduled time</li>
                            <li>Bring comfortable workout clothes and shoes</li>
                            <li>Don't forget to bring your booking ID</li>
                            <li>Payment can be made on-site</li>
                        </ul>
                        
                        <h3>Important Notes:</h3>
                        <ul>
                            <li>This booking ID is unique to your registration</li>
                            <li>Please keep this email for your records</li>
                            <li>For any queries, contact us at support@alldays.club</li>
                        </ul>
                        
                        <p>We're excited to see you at the event!</p>
                        
                        <p>Best regards,<br>
                        Team Alldays</p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated email. Please do not reply to this address.</p>
                        <p>© 2024 Alldays. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"""
Registration Confirmed - Alldays Event

Hi {first_name.title()} {last_name.title()},

Your registration for the Alldays event has been successfully confirmed!

Booking ID: {booking_id}

Registration Details:
- Name: {first_name.title()} {last_name.title()}
- Email: {recipient_email}
- Selected Sports: {sports_display}
- Event Date: {event_date}
- Event Location: {event_location}
{f'- Orangetheory Batch: {orangetheory_batch.title()}' if orangetheory_batch else ''}

What's Next?
- Please arrive 15 minutes before your scheduled time
- Bring comfortable workout clothes and shoes
- Don't forget to bring your booking ID
- Payment can be made on-site

Important Notes:
- This booking ID is unique to your registration
- Please keep this email for your records
- For any queries, contact us at support@alldays.club

We're excited to see you at the event!

Best regards,
Team Alldays

---
This is an automated email. Please do not reply to this address.
© 2024 Alldays. All rights reserved.
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Attach both HTML and text versions
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            response = self.ses_client.send_raw_email(
                Source=self.sender_email,
                Destinations=[recipient_email],
                RawMessage={'Data': msg.as_string()}
            )
            
            logger.info(f"Confirmation email sent successfully to {recipient_email}. Message ID: {response['MessageId']}")
            return True
            
        except NoCredentialsError:
            logger.error("AWS credentials not found for SES")
            return False
        except ClientError as e:
            logger.error(f"SES error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}", exc_info=True)
            return False

    def verify_email_identity(self, email: str) -> bool:
        """
        Verify an email address with SES
        """
        try:
            response = self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"Verification email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Error verifying email {email}: {e}")
            return False

    def get_send_quota(self) -> dict:
        """
        Get SES sending quota information
        """
        try:
            response = self.ses_client.get_send_quota()
            return {
                'max_24_hour_send': response['Max24HourSend'],
                'sent_last_24_hours': response['SentLast24Hours'],
                'max_send_rate': response['MaxSendRate'],
                'sending_enabled': response.get('SendingEnabled', False)
            }
        except Exception as e:
            logger.error(f"Error getting SES quota: {e}")
            return {}

# Create global instance
ses_email_service = SESEmailService()
