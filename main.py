# Core FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import os
import logging
import time
import random
import string
from datetime import datetime
from dotenv import load_dotenv
from fastapi.security.api_key import APIKeyHeader
from fastapi.openapi.utils import get_openapi
import re

# Database and model imports
from db.database import engine, Base, get_db, DBSession
from models import *  # Your database models
from models.event_registration_model import EventRegistrationModel
from models.user_registration_model import UserRegistrationModel
from models.sports_model import SportsModel
from models.jindal_registration_model import JindalRegistrationModel

# Schema imports
from schemas.event_registration_schema import EventRegistrationSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_registration_schema import UserRegistrationCreate, UserRegistrationResponse
from schemas.sports_schema import (
    SportsCreate, SportsResponse, SportsUpdate, 
    SportsAvailabilityResponse, SportsListResponse,
    TicketPurchaseRequest, TicketPurchaseResponse
)
from schemas.jindal_registration_schema import JindalRegistrationCreate, JindalRegistrationResponse, JindalRegistrationUpdate, JindalRegistrationListResponse

# Connector imports
from connector.connector import event_registration_connector, transaction_connector, user_registration_connector, sports_connector
from connector.sports_connector import sports_connector as sports_connector_instance
from connector.jindal_registration_connector import jindal_registration_connector

# AWS imports
import boto3
from botocore.exceptions import NoCredentialsError

# Utility imports
from utils.timezone_utils import format_ist_datetime
from utils.email_utils import ses_email_service

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(title="Alldays API", version="1.0.0")

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

# API Key configuration
API_KEY = os.environ.get("API_KEY", "default_key_for_development")
if not API_KEY:
    API_KEY = "default_key_for_development"  # Fallback for development

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        logger.warning("Unauthorized access attempt with API key: %s", api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Rate limiting
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

# Routes
@app.get('/')
def home():
    return {"message": "Alldays API is running"}

@app.options('/{full_path:path}')
async def options_handler(full_path: str):
    """Handle preflight CORS requests"""
    return {"message": "OK"}

# ============================================================================
# EVENT REGISTRATION ENDPOINTS (Preserved for existing application)
# ============================================================================

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
    """
    Create event registration (preserved for existing application)
    """
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
                s3_key = f"event_files/{email}_{first_name}_{last_name}.{file_ext}"
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
        
        # Send confirmation email
        email_sent = False
        try:
            email_sent = ses_email_service.send_confirmation_email(
                recipient_email=email,
                first_name=first_name,
                last_name=last_name,
                booking_id=booking_id,
                selected_sports=selected_sports,
                event_date=event_date,
                event_location=event_location,
                orangetheory_batch=orangetheory_batch
            )
            if email_sent:
                logger.info(f"Confirmation email sent successfully to {email}")
            else:
                logger.warning(f"Failed to send confirmation email to {email}")
        except Exception as email_error:
            logger.error(f"Error sending confirmation email to {email}: {email_error}", exc_info=True)
        
        return {
            "id": reg_obj.id, 
            "booking_id": booking_id, 
            "message": "Registration successful", 
            "file_url": file_url,
            "email_sent": email_sent
        }
    except Exception as e:
        logger.error(f"Error in event registration: {e}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "An unexpected error occurred. Please try again later or contact support."})

@app.post('/event-registration-with-email')
def create_event_registration_with_email(
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
    """
    Enhanced event registration endpoint with SES email confirmation
    """
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
                s3_key = f"event_files/{email}_{first_name}_{last_name}.{file_ext}"
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
        
        # Send confirmation email with enhanced error handling
        email_sent = False
        email_error_message = None
        try:
            email_sent = ses_email_service.send_confirmation_email(
                recipient_email=email,
                first_name=first_name,
                last_name=last_name,
                booking_id=booking_id,
                selected_sports=selected_sports,
                event_date=event_date,
                event_location=event_location,
                orangetheory_batch=orangetheory_batch
            )
            if email_sent:
                logger.info(f"Confirmation email sent successfully to {email}")
            else:
                logger.warning(f"Failed to send confirmation email to {email}")
                email_error_message = "Registration successful but email delivery failed"
        except Exception as email_error:
            logger.error(f"Error sending confirmation email to {email}: {email_error}", exc_info=True)
            email_error_message = f"Registration successful but email delivery failed: {str(email_error)}"
        
        response_data = {
            "id": reg_obj.id, 
            "booking_id": booking_id, 
            "message": "Registration successful", 
            "file_url": file_url,
            "email_sent": email_sent
        }
        
        if email_error_message:
            response_data["email_error"] = email_error_message
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in event registration with email: {e}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "An unexpected error occurred. Please try again later or contact support."})







@app.get('/registration-counts')
def get_registration_counts(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get registration counts for each sport to determine availability
    """
    check_rate_limit(request)
    
    try:
        registrations = db.query(EventRegistrationModel).all()
        
        # Count registrations for each sport
        sport_counts = {
            "orangetheory": 0,
            "strength": 0,
            "breathwork": 0
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
                    if "strength" in selected_sports_lower:
                        sport_counts["strength"] += 1
                    if "breathwork" in selected_sports_lower:
                        sport_counts["breathwork"] += 1
        
        # Set fixed limits for each sport
        sport_limits = {
            "orangetheory": 50,    # Limited capacity for Orangetheory
            "strength": 50,    # High limit for other sports
            "breathwork": 50    # High limit for other sports
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

@app.post('/transaction')
def create_transaction(
    request: TransactionSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Create transaction record (admin only)
    """
    try:
        txn_obj = transaction_connector.create(db, {
            'event_registration_id': request.event_registration_id,
            'amount': request.amount,
            'status': request.status,
            'razorpay_payment_id': request.razorpay_payment_id
        })
        return {"id": txn_obj.id, "message": "Transaction recorded"}
    except Exception as e:
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to create transaction. Please try again later."}
        )

# ============================================================================
# JINDAL REGISTRATION ENDPOINTS (Production Ready)
# ============================================================================

@app.post('/jindal-registration', response_model=JindalRegistrationResponse)
def create_jindal_registration(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    jgu_student_id: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    selected_sports: str = Form(...),  # JSON string of selected sports
    pickle_level: str = Form(None),
    total_amount: int = Form(...),
    agreed_to_terms: bool = Form(True),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """
    Create Jindal registration with file upload (single API endpoint)
    """
    check_rate_limit(request)
    
    try:
        # Validate phone number
        phone_digits = ''.join(filter(str.isdigit, phone))
        if len(phone_digits) < 10:
            raise HTTPException(
                status_code=422,
                detail="Invalid phone number. Must be at least 10 digits."
            )
        
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise HTTPException(
                status_code=422,
                detail="Invalid email format."
            )
        
        # Check if registration already exists
        existing_registration = jindal_registration_connector.get_by_email_or_jgu_id(
            db, email, jgu_student_id
        )
        if existing_registration:
            raise HTTPException(
                status_code=409,
                detail="Registration already exists with this email or JGU Student ID."
            )
        
        # Handle file upload if provided (following event registration pattern)
        payment_proof_url = None
        if file:
            try:
                # Validate file type
                if not file.content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=400,
                        detail="Only image files are allowed for payment proof"
                    )
                
                # Upload to S3 (following event registration pattern)
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                )
                bucket_name = os.environ.get('AWS_S3_BUCKET', 'alldayspayments')
                file_ext = file.filename.split('.')[-1]
                s3_key = f"jindalpayments/{email}_{first_name}_{last_name}.{file_ext}"
                s3.upload_fileobj(file.file, bucket_name, s3_key)
                payment_proof_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                logger.info(f"Payment proof uploaded to S3: {payment_proof_url}")
                
            except NoCredentialsError:
                logger.error("AWS credentials not found.")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    content={"detail": "AWS credentials not found. Please contact support."}
                )
            except Exception as s3e:
                logger.error(f"S3 upload failed: {s3e}", exc_info=True)
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    content={"detail": "File upload failed. Please try again later or contact support."}
                )
        
        # Parse selected_sports if it's a JSON string
        try:
            if selected_sports.startswith('['):
                selected_sports_list = json.loads(selected_sports)
            else:
                selected_sports_list = [selected_sports]
        except json.JSONDecodeError:
            selected_sports_list = [selected_sports]
        
        # Create registration data
        registration_data = {
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'email': email.lower().strip(),
            'phone': phone_digits,
            'jgu_student_id': jgu_student_id.upper().strip(),
            'city': city.strip(),
            'state': state.strip(),
            'selected_sports': selected_sports_list,
            'pickle_level': pickle_level.strip() if pickle_level else None,
            'total_amount': total_amount,
            'payment_status': 'pending',
            'payment_proof': payment_proof_url,
            'agreed_to_terms': agreed_to_terms
        }
        
        # Create registration
        registration = jindal_registration_connector.create_registration(db, registration_data)
        
        logger.info(f"Jindal registration created: id={registration.id}, email={email}, jgu_id={jgu_student_id}")
        
        return {
            "id": registration.id,
            "first_name": registration.first_name,
            "last_name": registration.last_name,
            "email": registration.email,
            "phone": registration.phone,
            "jgu_student_id": registration.jgu_student_id,
            "city": registration.city,
            "state": registration.state,
            "selected_sports": json.loads(registration.selected_sports) if registration.selected_sports else [],
            "pickle_level": registration.pickle_level,
            "total_amount": registration.total_amount,
            "payment_status": registration.payment_status,
            "payment_proof": registration.payment_proof,
            "agreed_to_terms": registration.agreed_to_terms,
            "created_at": registration.created_at,
            "updated_at": registration.updated_at,
            "message": "Registration successful",
            "payment_proof_url": payment_proof_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Jindal registration: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={"detail": "An unexpected error occurred. Please try again later or contact support."}
        )

@app.get('/jindal-registrations', response_model=JindalRegistrationListResponse)
def get_jindal_registrations(
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get all Jindal registrations (admin only)
    """
    check_rate_limit(request)
    
    try:
        registrations = db.query(JindalRegistrationModel).order_by(JindalRegistrationModel.created_at.desc()).all()
        
        registration_list = []
        for reg in registrations:
            registration_list.append({
                "id": reg.id,
                "first_name": reg.first_name,
                "last_name": reg.last_name,
                "email": reg.email,
                "phone": reg.phone,
                "jgu_student_id": reg.jgu_student_id,
                "city": reg.city,
                "state": reg.state,
                "selected_sports": json.loads(reg.selected_sports) if reg.selected_sports else [],
                "pickle_level": reg.pickle_level,
                "total_amount": reg.total_amount,
                "payment_status": reg.payment_status,
                "payment_proof": reg.payment_proof,
                "agreed_to_terms": reg.agreed_to_terms,
                "created_at": reg.created_at,
                "updated_at": reg.updated_at
            })
        
        return {
            "total_registrations": len(registration_list),
            "registrations": registration_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching Jindal registrations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch registrations. Please try again later."
        )

@app.get('/jindal-registration/{registration_id}')
def get_jindal_registration(
    request: Request,
    registration_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get specific Jindal registration (admin only)
    """
    check_rate_limit(request)
    
    try:
        registration = jindal_registration_connector.get_registration_with_sports(db, registration_id)
        
        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
        return registration
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Jindal registration {registration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch registration. Please try again later."
        )

@app.put('/jindal-registration/{registration_id}', response_model=JindalRegistrationResponse)
def update_jindal_registration(
    request: Request,
    registration_id: int,
    update_data: JindalRegistrationUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Update Jindal registration (admin only)
    """
    check_rate_limit(request)
    
    try:
        # Check if registration exists
        registration = db.query(JindalRegistrationModel).filter_by(id=registration_id).first()
        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle selected_sports conversion
        if 'selected_sports' in update_dict and isinstance(update_dict['selected_sports'], list):
            update_dict['selected_sports'] = json.dumps(update_dict['selected_sports'])
        
        # Update registration
        for field, value in update_dict.items():
            setattr(registration, field, value)
        
        db.commit()
        db.refresh(registration)
        
        logger.info(f"Updated Jindal registration {registration_id}")
        
        return {
            "id": registration.id,
            "first_name": registration.first_name,
            "last_name": registration.last_name,
            "email": registration.email,
            "phone": registration.phone,
            "jgu_student_id": registration.jgu_student_id,
            "city": registration.city,
            "state": registration.state,
            "selected_sports": json.loads(registration.selected_sports) if registration.selected_sports else [],
            "pickle_level": registration.pickle_level,
            "total_amount": registration.total_amount,
            "payment_status": registration.payment_status,
            "payment_proof": registration.payment_proof,
            "agreed_to_terms": registration.agreed_to_terms,
            "created_at": registration.created_at,
            "updated_at": registration.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Jindal registration {registration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update registration. Please try again later."
        )

@app.put('/jindal-registration/{registration_id}/payment')
def update_jindal_payment_status(
    request: Request,
    registration_id: int,
    payment_status: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Update payment status for Jindal registration (admin only)
    """
    check_rate_limit(request)
    
    try:
        # Validate payment status
        valid_statuses = ["pending", "completed", "failed"]
        if payment_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Payment status must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update payment status
        updated_registration = jindal_registration_connector.update_payment_status(
            db, registration_id, payment_status
        )
        
        if not updated_registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
        logger.info(f"Updated payment status for Jindal registration {registration_id} to {payment_status}")
        
        return {
            "success": True,
            "message": f"Payment status updated to {payment_status}",
            "registration_id": registration_id,
            "payment_status": payment_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment status for registration {registration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update payment status. Please try again later."
        )

@app.get('/jindal-registrations-summary')
def get_jindal_registrations_summary(
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get summary of Jindal registrations (admin only)
    """
    check_rate_limit(request)
    
    try:
        summary = jindal_registration_connector.get_registrations_summary(db)
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching Jindal registrations summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch registrations summary. Please try again later."
        )

# ============================================================================
# SPORTS ENDPOINTS (For future use)
# ============================================================================

@app.get('/sports', response_model=SportsListResponse)
def get_sports(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get all sports with availability status
    """
    check_rate_limit(request)
    
    try:
        all_sports = db.query(SportsModel).all()
        available_sports = [s for s in all_sports if s.is_available]
        sold_out_sports = [s for s in all_sports if s.is_sold_out]
        
        sports_list = []
        for sport in all_sports:
            sports_list.append({
                "sport_key": sport.sport_key,
                "sport_name": sport.sport_name,
                "price": sport.price,
                "current_count": sport.current_count,
                "max_capacity": sport.max_capacity,
                "remaining_tickets": sport.remaining_tickets,
                "is_available": sport.is_available,
                "is_sold_out": sport.is_sold_out,
                "timing": sport.timing
            })
        
        return {
            "total_sports": len(all_sports),
            "available_sports": len(available_sports),
            "sold_out_sports": len(sold_out_sports),
            "sports": sports_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching sports: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch sports. Please try again later."
        )

# SES Management Endpoints
@app.get('/ses/quota')
def get_ses_quota(request: Request):
    """
    Get SES sending quota information (admin endpoint)
    """
    check_rate_limit(request)
    try:
        quota_info = ses_email_service.get_send_quota()
        return {
            "quota_info": quota_info,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting SES quota: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to get SES quota information"}
        )

@app.post('/ses/verify-email')
def verify_email_identity(
    request: Request,
    email: str = Form(...)
):
    """
    Verify an email address with SES (admin endpoint)
    """
    check_rate_limit(request)
    try:
        success = ses_email_service.verify_email_identity(email)
        if success:
            return {
                "message": f"Verification email sent to {email}",
                "status": "success"
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Failed to send verification email to {email}"}
            )
    except Exception as e:
        logger.error(f"Error verifying email {email}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to verify email address"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)