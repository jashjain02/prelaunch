import boto3
import os
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from templates.email_templates import template_loader

logger = logging.getLogger(__name__)

class SESEmailService:
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'ap-south-1')
        )
        self.sender_email = os.environ.get('SES_SENDER_EMAIL', 'alldaysapp@gmail.com')
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
            
            # Prepare template variables
            template_vars = {
                'FIRST_NAME': first_name.title(),
                'LAST_NAME': last_name.title(),
                'EMAIL': recipient_email,
                'BOOKING_ID': booking_id,
                'SELECTED_SPORTS': sports_display,
                'EVENT_DATE': event_date,
                'EVENT_LOCATION': event_location,
                'ORANGETHEORY_BATCH_ROW': f'<div class="detail-row"><span class="detail-label">Orangetheory Batch:</span><span>{orangetheory_batch.title()}</span></div>' if orangetheory_batch else ''
            }
            
            # Create HTML email content using template
            html_content = template_loader.fill_template('event_registration', template_vars)
            
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

    def send_jindal_confirmation_email(self, 
                                      recipient_email: str, 
                                      first_name: str, 
                                      last_name: str, 
                                      jgu_student_id: str,
                                      selected_sports: str, 
                                      total_amount: int,
                                      city: str,
                                      state: str,
                                      pickle_level: Optional[str] = None) -> bool:
        """
        Send confirmation email for Jindal registration
        """
        try:
            # Create email content
            subject = f"Jindal Registration Confirmed - Alldays Event (ID: {jgu_student_id})"
            
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
            
            # Prepare template variables
            template_vars = {
                'FIRST_NAME': first_name.title(),
                'LAST_NAME': last_name.title(),
                'EMAIL': recipient_email,
                'JGU_STUDENT_ID': jgu_student_id,
                'CITY': city.title(),
                'STATE': state.title(),
                'SELECTED_SPORTS': sports_display,
                'TOTAL_AMOUNT': total_amount,
                'PICKLEBALL_LEVEL_ROW': f'<div class="detail-row"><span class="detail-label">Pickleball Level:</span><span>{pickle_level.title()}</span></div>' if pickle_level else ''
            }
            
            # Create HTML email content using template
            html_content = template_loader.fill_template('jindal_registration', template_vars)
            
            # Create plain text version
            text_content = f"""
Jindal Registration Confirmed - Alldays Event

Hi {first_name.title()} {last_name.title()},

Your registration for the Alldays x Jindal event has been successfully confirmed!

JGU Student ID: {jgu_student_id}

Registration Details:
- Name: {first_name.title()} {last_name.title()}
- Email: {recipient_email}
- JGU Student ID: {jgu_student_id}
- Location: {city.title()}, {state.title()}
- Selected Sports: {sports_display}
{f'- Pickleball Level: {pickle_level.title()}' if pickle_level else ''}
- Total Amount: ₹{total_amount}

What's Next?
- Please arrive 15 minutes before your scheduled time
- Bring comfortable workout clothes and shoes
- Don't forget to bring your JGU Student ID
- Payment proof has been uploaded successfully

Important Notes:
- This registration is linked to your JGU Student ID
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
            
            logger.info(f"Jindal confirmation email sent successfully to {recipient_email}. Message ID: {response['MessageId']}")
            return True
            
        except NoCredentialsError:
            logger.error("AWS credentials not found for SES")
            return False
        except ClientError as e:
            logger.error(f"SES error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Jindal confirmation email: {e}", exc_info=True)
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
        Get SES sending quota information using SES v2 API
        """
        try:
            # Use SES v2 client for better account information
            ses_v2_client = boto3.client(
                'sesv2',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION', 'ap-south-1')
            )
            
            # Get account information using SES v2
            account_response = ses_v2_client.get_account()
            
            # Get quota information using SES v1 (for compatibility)
            quota_response = self.ses_client.get_send_quota()
            
            return {
                'max_24_hour_send': quota_response['Max24HourSend'],
                'sent_last_24_hours': quota_response['SentLast24Hours'],
                'max_send_rate': quota_response['MaxSendRate'],
                'sending_enabled': account_response.get('SendingEnabled', False),
                'production_access_enabled': account_response.get('ProductionAccessEnabled', False),
                'enforcement_status': account_response.get('EnforcementStatus', 'UNKNOWN')
            }
        except Exception as e:
            logger.error(f"Error getting SES quota: {e}")
            return {}

# Create global instance
ses_email_service = SESEmailService()
