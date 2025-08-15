# Core FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import os
from db.database import engine, Base, get_db, DBSession
from models import *  # Your database models
from models.event_registration_model import EventRegistrationModel
from models.user_registration_model import UserRegistrationModel
from models.sports_model import SportsModel
from schemas.event_registration_schema import EventRegistrationSchema
from schemas.transaction_schema import TransactionSchema
from schemas.user_registration_schema import UserRegistrationCreate, UserRegistrationResponse
from schemas.sports_schema import (
    SportsCreate, SportsResponse, SportsUpdate, 
    SportsAvailabilityResponse, SportsListResponse,
    TicketPurchaseRequest, TicketPurchaseResponse
)
from schemas.jindal_registration_schema import JindalRegistrationCreate, JindalRegistrationResponse, JindalRegistrationUpdate, JindalRegistrationListResponse
from connector.connector import event_registration_connector, transaction_connector, user_registration_connector, sports_connector
from connector.sports_connector import sports_connector as sports_connector_instance
from connector.jindal_registration_connector import jindal_registration_connector
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
app = FastAPI(title="Your API", version="1.0.0")

# CORS origins - allow all origins for development
origins = ["*"]

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
    pickleball_level: str = Form(None),
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
                s3_key = f"jindalpayments/{email}_{first_name}_{last_name}.{file_ext}"
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
                'pickleball_level': pickleball_level.lower(),
                'file_url': file_url,
                'booking_id': booking_id
            })
        except Exception as dbe:
            logger.error(f"Database error during registration: {dbe}", exc_info=True)
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Registration failed due to a server error. Please try again later."})
        logger.info(f"Event registration created: id={reg_obj.id}, booking_id={booking_id}, email={email}")
        return {"id": reg_obj.id, "booking_id": booking_id, "message": "Registration successful", "file_url": file_url}
    except Exception as e:
        logger.error(f"Error in event registration: {e}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "An unexpected error occurred. Please try again later or contact support."})

@app.post('/transaction')
def create_transaction(
    request: TransactionSchema,
    db: Session = Depends(get_db),
):
    try:
        txn_obj = transaction_connector.create(db, {
            'event_registration_id': request.event_registration_id,
            'amount': request.amount,
            'status': request.status,
            'razorpay_payment_id': request.razorpay_payment_id
        })
        return {"id": txn_obj.id, "message": "Transaction recorded"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})



@app.get('/registrations')
def get_all_registrations(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get all event registrations as JSON data
    """
    check_rate_limit(request)
    
    try:
        registrations = db.query(EventRegistrationModel).order_by(EventRegistrationModel.created_at.desc()).all()
        
        registration_list = []
        for reg in registrations:
            registration_list.append({
                "id": reg.id,
                "booking_id": reg.booking_id,
                "first_name": reg.first_name.title(),
                "last_name": reg.last_name.title(),
                "email": reg.email,
                "phone": reg.phone,
                "selected_sports": reg.selected_sports,
                "pickleball_level": reg.pickleball_level.title() if reg.pickleball_level else None,
                "file_url": reg.file_url,
                "created_at": format_ist_datetime(reg.created_at)
            })
        
        return {
            "total_count": len(registration_list),
            "registrations": registration_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching registrations: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch registrations. Please try again later."}
        )

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
            "pickleball": 0,
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
                    if "pickleball" in selected_sports_lower:
                        sport_counts["pickleball"] += 1
                    if "strength" in selected_sports_lower:
                        sport_counts["strength"] += 1
                    if "breathwork" in selected_sports_lower:
                        sport_counts["breathwork"] += 1
        
        # Set fixed limits for each sport
        sport_limits = {
            "pickleball": 0,   # Sold out - no more bookings allowed
            "strength": 50,    # High limit for other sports
            "breathwork": 50
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
            "availability": availability,
            "limits": sport_limits
        }
        
    except Exception as e:
        logger.error(f"Error fetching registration counts: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch registration counts. Please try again later."}
        )

@app.post('/user-registration', response_model=UserRegistrationResponse)
def create_user_registration(
    request: Request,
    user_data: UserRegistrationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user registration with form validation
    """
    check_rate_limit(request)
    
    try:
        # Check if email already exists
        existing_user = db.query(UserRegistrationModel).filter_by(email=user_data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create new user registration
        user_obj = user_registration_connector.create(db, {
            'first_name': user_data.first_name.lower(),
            'last_name': user_data.last_name.lower(),
            'email': user_data.email.lower(),
            'phone': user_data.phone,
            'jgu_student_id': user_data.jgu_student_id,
            'city': user_data.city.lower(),
            'state': user_data.state,
            'agreed_to_terms': user_data.agreed_to_terms
        })
        
        logger.info(f"User registration created: id={user_obj.id}, email={user_data.email}")
        return user_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user registration: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later or contact support."}
        )

@app.get('/user-registrations')
def get_all_user_registrations(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get all user registrations as JSON data (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        users = db.query(UserRegistrationModel).order_by(UserRegistrationModel.created_at.desc()).all()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "first_name": user.first_name.title(),
                "last_name": user.last_name.title(),
                "email": user.email,
                "phone": user.phone,
                "jgu_student_id": user.jgu_student_id,
                "city": user.city.title(),
                "state": user.state,
                "agreed_to_terms": user.agreed_to_terms,
                "created_at": format_ist_datetime(user.created_at),
                "updated_at": format_ist_datetime(user.updated_at)
            })
        
        return {
            "total_count": len(user_list),
            "users": user_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching user registrations: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch user registrations. Please try again later."}
        )

# Sports Management Endpoints
@app.post('/sports', response_model=SportsResponse)
def create_sport(
    request: Request,
    sport_data: SportsCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new sport (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        # Check if sport_key already exists
        existing_sport = db.query(SportsModel).filter_by(sport_key=sport_data.sport_key).first()
        if existing_sport:
            raise HTTPException(
                status_code=400,
                detail=f"Sport with key '{sport_data.sport_key}' already exists"
            )
        
        sport_obj = sports_connector.create(db, {
            'sport_name': sport_data.sport_name,
            'sport_key': sport_data.sport_key,
            'description': sport_data.description,
            'price': sport_data.price,
            'max_capacity': sport_data.max_capacity,
            'timing': sport_data.timing,
            'is_active': sport_data.is_active
        })
        
        logger.info(f"Sport created: {sport_obj.sport_name} with capacity {sport_obj.max_capacity}")
        return sport_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sport: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.get('/sports', response_model=SportsListResponse)
def get_all_sports(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get all sports with availability status
    """
    check_rate_limit(request)
    
    try:
        sports = db.query(SportsModel).order_by(SportsModel.sport_name).all()
        
        sports_list = []
        for sport in sports:
            sports_list.append({
                "sport_key": sport.sport_key,
                "sport_name": sport.sport_name,
                "description": sport.description,
                "price": sport.price,
                "current_count": sport.current_count,
                "max_capacity": sport.max_capacity,
                "remaining_tickets": sport.remaining_tickets,
                "is_available": sport.is_available,
                "is_sold_out": sport.is_sold_out,
                "timing": sport.timing
            })
        
        available_count = len([s for s in sports if s.is_available])
        sold_out_count = len([s for s in sports if s.is_sold_out])
        
        return {
            "total_sports": len(sports_list),
            "available_sports": available_count,
            "sold_out_sports": sold_out_count,
            "sports": sports_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching sports: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch sports. Please try again later."}
        )

@app.get('/sports/{sport_key}', response_model=SportsAvailabilityResponse)
def get_sport_by_key(
    request: Request,
    sport_key: str,
    db: Session = Depends(get_db),
):
    """
    Get specific sport by sport_key
    """
    check_rate_limit(request)
    
    try:
        sport = sports_connector_instance.get_by_sport_key(db, sport_key)
        if not sport:
            raise HTTPException(
                status_code=404,
                detail=f"Sport '{sport_key}' not found"
            )
        
        return {
            "sport_key": sport.sport_key,
            "sport_name": sport.sport_name,
            "description": sport.description,
            "price": sport.price,
            "current_count": sport.current_count,
            "max_capacity": sport.max_capacity,
            "remaining_tickets": sport.remaining_tickets,
            "is_available": sport.is_available,
            "is_sold_out": sport.is_sold_out,
            "timing": sport.timing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sport {sport_key}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch sport. Please try again later."}
        )

@app.post('/sports/{sport_key}/purchase', response_model=TicketPurchaseResponse)
def purchase_tickets(
    request: Request,
    sport_key: str,
    purchase_data: TicketPurchaseRequest,
    db: Session = Depends(get_db),
):
    """
    Purchase tickets for a specific sport
    """
    check_rate_limit(request)
    
    try:
        success, message, sport = sports_connector_instance.purchase_tickets(
            db, sport_key, purchase_data.quantity
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=message
            )
        
        return {
            "success": True,
            "sport_key": sport.sport_key,
            "sport_name": sport.sport_name,
            "quantity": purchase_data.quantity,
            "total_price": sport.price * purchase_data.quantity,
            "remaining_tickets": sport.remaining_tickets,
            "is_sold_out": sport.is_sold_out,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing tickets for {sport_key}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.post('/sports/{sport_key}/refund')
def refund_tickets(
    request: Request,
    sport_key: str,
    quantity: int = 1,
    db: Session = Depends(get_db),
):
    """
    Refund tickets for a specific sport (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        success, message, sport = sports_connector_instance.refund_tickets(db, sport_key, quantity)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=message
            )
        
        return {
            "success": True,
            "message": message,
            "sport_key": sport.sport_key,
            "sport_name": sport.sport_name,
            "refunded_quantity": quantity,
            "remaining_tickets": sport.remaining_tickets,
            "is_sold_out": sport.is_sold_out
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refunding tickets for {sport_key}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.post('/sports/{sport_key}/reset')
def reset_sport_count(
    request: Request,
    sport_key: str,
    db: Session = Depends(get_db),
):
    """
    Reset ticket count for a sport (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        success, message, sport = sports_connector_instance.reset_sport_count(db, sport_key)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=message
            )
        
        return {
            "success": True,
            "message": message,
            "sport_key": sport.sport_key,
            "sport_name": sport.sport_name,
            "current_count": sport.current_count,
            "is_sold_out": sport.is_sold_out
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting sport count for {sport_key}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.get('/sports-summary')
def get_sports_summary(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get summary of all sports (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        summary = sports_connector_instance.get_sports_summary(db)
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching sports summary: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"detail": "Failed to fetch sports summary. Please try again later."}
        )

# Jindal Registration Endpoints
@app.post('/jindal-registration', response_model=JindalRegistrationResponse)
def create_jindal_registration(
    request: Request,
    registration_data: JindalRegistrationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new Jindal registration
    """
    check_rate_limit(request)
    
    try:
        # Check if email already exists
        existing_email = jindal_registration_connector.get_by_email(db, registration_data.email)
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Check if JGU Student ID already exists
        existing_jgu_id = jindal_registration_connector.get_by_jgu_id(db, registration_data.jgu_student_id)
        if existing_jgu_id:
            raise HTTPException(
                status_code=400,
                detail="JGU Student ID already registered"
            )
        
        # Create registration
        registration = jindal_registration_connector.create_registration(db, registration_data.dict())
        
        # Format timestamps for response
        registration.created_at = format_ist_datetime(registration.created_at)
        registration.updated_at = format_ist_datetime(registration.updated_at)
        
        return registration
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Jindal registration: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.get('/jindal-registrations', response_model=JindalRegistrationListResponse)
def get_all_jindal_registrations(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get all Jindal registrations (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        registrations = jindal_registration_connector.get_all(db)
        
        # Format timestamps for response
        for registration in registrations:
            registration.created_at = format_ist_datetime(registration.created_at)
            registration.updated_at = format_ist_datetime(registration.updated_at)
        
        return {
            "total_registrations": len(registrations),
            "registrations": registrations
        }
        
    except Exception as e:
        logger.error(f"Error fetching Jindal registrations: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to fetch registrations. Please try again later."}
        )

@app.get('/jindal-registration/{registration_id}')
def get_jindal_registration(
    request: Request,
    registration_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific Jindal registration by ID
    """
    check_rate_limit(request)
    
    try:
        registration = jindal_registration_connector.get_registration_with_sports(db, registration_id)
        
        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
        # Format timestamps
        registration['created_at'] = format_ist_datetime(registration['created_at'])
        registration['updated_at'] = format_ist_datetime(registration['updated_at'])
        
        return registration
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Jindal registration {registration_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.put('/jindal-registration/{registration_id}', response_model=JindalRegistrationResponse)
def update_jindal_registration(
    request: Request,
    registration_id: int,
    registration_data: JindalRegistrationUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a Jindal registration
    """
    check_rate_limit(request)
    
    try:
        # Check if registration exists
        existing_registration = jindal_registration_connector.get_by_id(db, registration_id)
        if not existing_registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
        # Update registration
        updated_registration = jindal_registration_connector.update(db, registration_id, registration_data.dict(exclude_unset=True))
        
        # Format timestamps for response
        updated_registration.created_at = format_ist_datetime(updated_registration.created_at)
        updated_registration.updated_at = format_ist_datetime(updated_registration.updated_at)
        
        return updated_registration
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Jindal registration {registration_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.put('/jindal-registration/{registration_id}/payment')
def update_payment_status(
    request: Request,
    registration_id: int,
    payment_status: str,
    payment_proof: str = None,
    db: Session = Depends(get_db),
):
    """
    Update payment status for a Jindal registration
    """
    check_rate_limit(request)
    
    try:
        updated_registration = jindal_registration_connector.update_payment_status(
            db, registration_id, payment_status, payment_proof
        )
        
        if not updated_registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
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
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

@app.get('/jindal-registrations-summary')
def get_jindal_registrations_summary(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get summary of all Jindal registrations (admin endpoint)
    """
    check_rate_limit(request)
    
    try:
        summary = jindal_registration_connector.get_registrations_summary(db)
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching Jindal registrations summary: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to fetch registrations summary. Please try again later."}
        )

@app.post('/jindal-registration/{registration_id}/upload-payment')
def upload_jindal_payment_proof(
    request: Request,
    registration_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload payment proof for a Jindal registration
    """
    check_rate_limit(request)
    
    try:
        # Check if registration exists
        registration = jindal_registration_connector.get_by_id(db, registration_id)
        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found"
            )
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"jindal_payment_{registration_id}_{int(time.time())}.{file_extension}"
        
        # S3 path for Jindal payments
        s3_key = f"alldayspayments/jindalpayments/{unique_filename}"
        
        # Upload to S3
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            # Read file content
            file_content = file.file.read()
            
            # Upload to S3
            s3_client.put_object(
                Bucket=os.getenv('AWS_S3_BUCKET'),
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type,
                ACL='public-read'
            )
            
            # Generate S3 URL
            s3_url = f"https://{os.getenv('AWS_S3_BUCKET')}.s3.amazonaws.com/{s3_key}"
            
            # Update registration with payment proof URL
            updated_registration = jindal_registration_connector.update_payment_status(
                db, registration_id, "pending", s3_url
            )
            
            logger.info(f"Uploaded payment proof for Jindal registration {registration_id} to S3: {s3_url}")
            
            return {
                "success": True,
                "message": "Payment proof uploaded successfully",
                "registration_id": registration_id,
                "payment_proof_url": s3_url,
                "s3_key": s3_key
            }
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return JSONResponse(
                status_code=500,
                content={"detail": "AWS credentials not configured"}
            )
        except Exception as s3_error:
            logger.error(f"S3 upload error: {s3_error}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Failed to upload file to S3"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading payment proof for registration {registration_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)