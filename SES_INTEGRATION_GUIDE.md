# SES Email Integration Guide

## Overview

This guide explains how to set up and use AWS SES (Simple Email Service) for sending confirmation emails when users register for events.

## Features

### ✅ **Email Confirmation System**
- Automatic confirmation emails sent after successful registration
- Beautiful HTML email templates with Alldays branding
- Plain text fallback for email clients that don't support HTML
- Detailed registration information included in emails

### 📧 **Email Content**

#### Event Registration Emails
- Registration confirmation with booking ID
- Event details (date, location, selected sports)
- Orangetheory batch information (if applicable)
- Next steps and important notes
- Contact information

#### Jindal Registration Emails
- Registration confirmation with JGU Student ID
- Event details (location, selected sports, pickleball level)
- Payment information and amount
- Next steps and important notes
- Contact information

## Setup Instructions

### 1. AWS SES Configuration

#### Step 1: Create AWS SES Account
1. Go to AWS Console → SES (Simple Email Service)
2. Choose your region (recommended: ap-south-1 for Mumbai)
3. Move out of sandbox mode (request production access)

#### Step 2: Verify Email Addresses
1. In SES Console, go to "Verified identities"
2. Add and verify your sender email: `alldaysapp@gmail.com`
3. Verify recipient emails for testing

#### Step 3: Configure Environment Variables
Add these to your `.env` file:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1

# SES Configuration
SES_SENDER_EMAIL=alldaysapp@gmail.com
SES_VERIFIED_EMAILS=test@example.com,admin@alldays.club
```

### 2. API Endpoints

#### Event Registration Endpoint with Email
```http
POST /event-registration-with-email
Content-Type: multipart/form-data

Parameters:
- first_name (required): User's first name
- last_name (required): User's last name
- email (required): User's email address
- phone (required): User's phone number
- selected_sports (required): JSON string of selected sports
- orangetheory_batch (optional): "batch1" or "batch2"
- event_date (optional): Event date
- event_location (optional): Event location
- file (optional): Payment screenshot
```

**Response:**
```json
{
  "id": 123,
  "booking_id": "ABC12345",
  "message": "Registration successful",
  "file_url": "https://...",
  "email_sent": true
}
```

#### Jindal Registration Endpoint (Original - No Email)
```http
POST /jindal-registration
Content-Type: multipart/form-data

Parameters:
- first_name (required): User's first name
- last_name (required): User's last name
- email (required): User's email address
- phone (required): User's phone number
- jgu_student_id (required): JGU Student ID
- city (required): City
- state (required): State
- selected_sports (required): JSON string of selected sports
- pickle_level (optional): Pickleball level
- total_amount (required): Total amount
- agreed_to_terms (required): Terms agreement
- file (optional): Payment proof
```

**Response:**
```json
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "jgu_student_id": "JGU2024001",
  "message": "Registration successful",
  "payment_proof_url": "https://..."
}
```

#### Jindal Registration Endpoint with Email (New)
```http
POST /jindal-registration-with-email
Content-Type: multipart/form-data

Parameters:
- first_name (required): User's first name
- last_name (required): User's last name
- email (required): User's email address
- phone (required): User's phone number
- jgu_student_id (required): JGU Student ID
- city (required): City
- state (required): State
- selected_sports (required): JSON string of selected sports
- pickle_level (optional): Pickleball level
- total_amount (required): Total amount
- agreed_to_terms (required): Terms agreement
- file (optional): Payment proof
```

**Response:**
```json
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "jgu_student_id": "JGU2024001",
  "message": "Registration successful",
  "payment_proof_url": "https://...",
  "email_sent": true
}
```

#### SES Management Endpoints

**Get SES Quota:**
```http
GET /ses/quota
```

**Get SES Account Details:**
```http
GET /ses/account
```

**Verify Email Address:**
```http
POST /ses/verify-email
Content-Type: application/x-www-form-urlencoded

email=test@example.com
```

### 3. Email Template Features

#### HTML Email Template
- Responsive design with Alldays branding
- Gradient header with brand colors
- Structured registration details
- Clear call-to-action sections
- Professional footer

#### Plain Text Fallback
- Clean, readable format
- All essential information included
- Compatible with all email clients

## Testing

### 1. Run Test Script
```bash
cd backend
python test_ses_integration.py
```

### 2. Manual Testing
1. Start your FastAPI server
2. Use the test script or make direct API calls
3. Check email delivery in your inbox
4. Verify email content and formatting

### 3. SES Console Monitoring
1. Check SES Console for delivery statistics
2. Monitor bounce and complaint rates
3. Review sending quotas and limits

## Error Handling

### Email Delivery Failures
- Registration still succeeds even if email fails
- Error details logged for debugging
- Response includes `email_sent` status
- Optional `email_error` field for detailed error info

### Common Issues
1. **Unverified Email**: Recipient email not verified in SES
2. **Sandbox Mode**: SES account still in sandbox (limited to verified emails)
3. **Rate Limits**: Exceeding SES sending limits
4. **AWS Credentials**: Incorrect or missing AWS credentials

## Production Deployment

### 1. Environment Setup
```bash
# Production environment variables
AWS_ACCESS_KEY_ID=your_production_key
AWS_SECRET_ACCESS_KEY=your_production_secret
AWS_REGION=ap-south-1
SES_SENDER_EMAIL=alldaysapp@gmail.com
```

### 2. SES Production Access
1. Request production access from AWS
2. Provide business use case details
3. Wait for approval (usually 24-48 hours)

### 3. Domain Verification (Recommended)
1. Verify your domain with SES
2. Set up DKIM authentication
3. Configure SPF and DMARC records

## Monitoring and Maintenance

### 1. Logs
- Email sending attempts logged with success/failure
- Detailed error messages for debugging
- Message IDs for tracking

### 2. Metrics to Monitor
- Email delivery success rate
- Bounce and complaint rates
- SES quota usage
- API response times

### 3. Maintenance Tasks
- Regular quota monitoring
- Bounce and complaint handling
- Template updates as needed
- Performance optimization

## Troubleshooting

### Email Not Received
1. Check SES Console for delivery status
2. Verify recipient email is correct
3. Check spam/junk folders
4. Ensure SES account is out of sandbox

### SES Errors
1. Verify AWS credentials
2. Check SES region configuration
3. Ensure email addresses are verified
4. Monitor SES quotas and limits

### API Errors
1. Check server logs for detailed error messages
2. Verify environment variables
3. Test SES connectivity
4. Check rate limiting

## Security Considerations

### 1. AWS Credentials
- Use IAM roles with minimal required permissions
- Rotate access keys regularly
- Never commit credentials to version control

### 2. Email Security
- Implement SPF, DKIM, and DMARC
- Monitor for email abuse
- Handle bounces and complaints properly

### 3. Data Protection
- Encrypt sensitive data in emails
- Follow GDPR/privacy regulations
- Implement proper data retention policies

## Support

For issues with SES integration:
1. Check AWS SES documentation
2. Review server logs for error details
3. Test with verified email addresses
4. Contact AWS support if needed

---

**Note**: This integration provides a robust email confirmation system that enhances user experience while maintaining reliability and security.
