#!/usr/bin/env python3
"""
Test script for SES email integration
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000"  # Change this to your API URL
TEST_EMAIL = "test@example.com"  # Change this to a verified email

def test_ses_quota():
    """Test SES quota endpoint"""
    print("Testing SES quota endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/ses/quota")
        if response.status_code == 200:
            data = response.json()
            print("✅ SES quota endpoint working")
            print(f"Quota info: {data}")
        else:
            print(f"❌ SES quota endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing SES quota: {e}")

def test_email_verification():
    """Test email verification endpoint"""
    print("\nTesting email verification endpoint...")
    try:
        data = {"email": TEST_EMAIL}
        response = requests.post(f"{BASE_URL}/ses/verify-email", data=data)
        if response.status_code == 200:
            print("✅ Email verification endpoint working")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Email verification endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing email verification: {e}")

def test_registration_with_email():
    """Test registration with email endpoint"""
    print("\nTesting registration with email endpoint...")
    try:
        data = {
            "first_name": "Test",
            "last_name": "User",
            "email": TEST_EMAIL,
            "phone": "9876543210",
            "selected_sports": '["orangetheory"]',
            "orangetheory_batch": "batch1",
            "event_date": "24th August 2025",
            "event_location": "Orangetheory Fitness, Worli"
        }
        
        response = requests.post(f"{BASE_URL}/event-registration-with-email", data=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Registration with email endpoint working")
            print(f"Registration ID: {result.get('id')}")
            print(f"Booking ID: {result.get('booking_id')}")
            print(f"Email sent: {result.get('email_sent')}")
            if result.get('email_error'):
                print(f"Email error: {result.get('email_error')}")
        else:
            print(f"❌ Registration with email endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing registration with email: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing SES Email Integration")
    print("=" * 50)
    
    # Check if required environment variables are set
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these variables in your .env file")
        return
    
    print("✅ Environment variables configured")
    
    # Run tests
    test_ses_quota()
    test_email_verification()
    test_registration_with_email()
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")

if __name__ == "__main__":
    main()
