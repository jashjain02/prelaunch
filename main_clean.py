# Core FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import os
from db.database import engine, Base, get_db, DBSession
from models.event_registration_model import EventRegistrationModel
from schemas.event_registration_schema import EventRegistrationSchema
from connector.connector import event_registration_connector
import boto3
from botocore.exceptions import NoCredentialsError
import random
import string
from dotenv import load_dotenv
import logging
load_dotenv()
from fastapi.security.api_key import APIKeyHeader
import time
from fastapi.openapi.utils import get_openapi
from datetime import datetime
from utils.timezone_utils import format_ist_datetime

# FastAPI app initialization
app = FastAPI(title="Alldays Orangetheory Event API", version="1.0.0")

# CORS origins - allow specific origins for production
origins = [
    "https://prelaunch.alldays.club",
    "https://alldays.club",
    "http://localhost:3000",
    "http://localhost:5173",
    "*"  # Keep wildcard for development
]

# Create database tables
Base.metadata.create_all(engine)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Favicon path
favicon_path = 'favicon.ico'

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger("alldays_backend")

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Routes
@app.get('/')
def home():
    return {"message": "API is running"}

@app.options('/{full_path:path}')
async def options_handler(full_path: str):
    """Handle preflight CORS requests"""
    return {"message": "OK"}

# Simple in-memory rate limiter (per-process, per-IP, per-endpoint)
RATE_LIMIT = 5  # max requests
RATE_PERIOD = 60  # seconds
rate_limit_store = {}

def check_rate_limit(request: Request):
    ip = request.client.host
    endpoint = request.url.path
    key = f"{ip}:{endpoint}"
    now = time.time()
    window = rate_limit_store.get(key, [])
    # Remove timestamps outside the window
    window = [ts for ts in window if now - ts < RATE_PERIOD]
    if len(window) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for {ip} on {endpoint}")
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    window.append(now)
    rate_limit_store[key] = window

@app.post('/event-registration')
def create_event_registration(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    selected_sports: str = Form(...),
    orangetheory_batch: str = Form(None),
    event_date: str = Form("24th August 2025"),
    event_location: str = Form("Orangetheory Fitness, Worli"),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    check_rate_limit(request)
    try:
        file_url = None
        if file:
            try:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                )
                bucket_name = os.environ.get('S3_BUCKET_NAME', 'alldayspayments')
                file_ext = file.filename.split('.')[-1]
                s3_key = f"orangetheorypayments/{email}_{first_name}_{last_name}.{file_ext}"
                s3.upload_fileobj(file.file, bucket_name, s3_key)
                file_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                logger.info(f"File uploaded to S3: {file_url}")
            except NoCredentialsError:
                logger.error("AWS credentials not found.")
                return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "AWS credentials not found. Please contact support."})
            except Exception as s3e:
                logger.error(f"S3 upload failed: {s3e}", exc_info=True)
                return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "File upload failed. Please try again later or contact support."})
        
        # Generate unique 8-character alphanumeric booking_id
        def generate_booking_id():
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        booking_id = generate_booking_id()
        # Ensure uniqueness
        attempts = 0
        while db.query(EventRegistrationModel).filter_by(booking_id=booking_id).first():
            booking_id = generate_booking_id()
            attempts += 1
            if attempts > 5:
                logger.error("Failed to generate unique booking ID after 5 attempts.")
                return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Could not generate a unique booking ID. Please try again."})
        
        try:
            reg_obj = event_registration_connector.create(db, {
                'first_name': first_name.lower(),
                'last_name': last_name.lower(),
                'email': email.lower(),
                'phone': phone.lower(),
                'selected_sports': selected_sports.lower(),
                'orangetheory_batch': orangetheory_batch.lower() if orangetheory_batch else None,
                'event_date': event_date,
                'event_location': event_location,
                'payment_status': 'pending',
                'file_url': file_url,
                'booking_id': booking_id,
                'is_active': True
            })
        except Exception as dbe:
            logger.error(f"Database error during registration: {dbe}", exc_info=True)
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Registration failed due to a server error. Please try again later."})
        
        logger.info(f"Event registration created: id={reg_obj.id}, booking_id={booking_id}, email={email}")
        return {"id": reg_obj.id, "booking_id": booking_id, "message": "Registration successful", "file_url": file_url}
    except Exception as e:
        logger.error(f"Error in event registration: {e}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "An unexpected error occurred. Please try again later or contact support."})

@app.get('/registration-counts')
def get_registration_counts(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get registration counts for Orangetheory event to determine availability
    """
    check_rate_limit(request)
    
    try:
        registrations = db.query(EventRegistrationModel).all()
        
        # Count registrations for Orangetheory event
        sport_counts = {
            "orangetheory": 0
        }
        
        for reg in registrations:
            # Parse selected_sports (it's stored as a JSON string)
            try:
                selected_sports = json.loads(reg.selected_sports)
                if isinstance(selected_sports, list):
                    for sport in selected_sports:
                        if sport in sport_counts:
                            sport_counts[sport] += 1
                elif isinstance(selected_sports, str):
                    # Handle case where it might be a comma-separated string
                    sports_list = [s.strip().lower() for s in selected_sports.split(',')]
                    for sport in sports_list:
                        if sport in sport_counts:
                            sport_counts[sport] += 1
            except (json.JSONDecodeError, AttributeError):
                # If parsing fails, try to check if it contains the sport name
                if reg.selected_sports:
                    selected_sports_lower = reg.selected_sports.lower()
                    if "orangetheory" in selected_sports_lower:
                        sport_counts["orangetheory"] += 1
        
        # Set fixed limits for Orangetheory event
        sport_limits = {
            "orangetheory": 50   # Available for bookings
        }
        
        # Calculate availability
        availability = {}
        for sport, count in sport_counts.items():
            limit = sport_limits.get(sport, 50)
            remaining = max(0, limit - count)
            is_available = count < limit
            availability[sport] = {
                "current_count": count,
                "limit": limit,
                "available": is_available,
                "remaining": remaining
            }
            logger.info(f"Sport: {sport}, Count: {count}, Limit: {limit}, Available: {is_available}, Remaining: {remaining}")
        
        return {
            "sport_counts": sport_counts,
            "availability": availability
        }
        
    except Exception as e:
        logger.error(f"Error fetching registration counts: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch registration counts. Please try again later."}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
