# Core FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import os
from db.database import engine, Base, get_db, DBSession
from models import *  # Your database models
from schemas.event_registration_schema import EventRegistrationSchema
from schemas.transaction_schema import TransactionSchema
from connector.connector import event_registration_connector, transaction_connector
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

# FastAPI app initialization
app = FastAPI(title="Your API", version="1.0.0")

# CORS origins
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
@app.get('/favicon.ico')
def favicon():
    return FileResponse(favicon_path)

@app.get('/')
def home():
    return {"message": "API is running"}

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
        while db.query(models.event_registration_model.EventRegistrationModel).filter_by(booking_id=booking_id).first():
            booking_id = generate_booking_id()
            attempts += 1
            if attempts > 5:
                logger.error("Failed to generate unique booking ID after 5 attempts.")
                return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Could not generate a unique booking ID. Please try again."})
        try:
            reg_obj = event_registration_connector.create(db, {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'selected_sports': selected_sports,
                'pickleball_level': pickleball_level,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)