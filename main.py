# Core FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, Request
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

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
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

@app.post('/event-registration')
def create_event_registration(request: EventRegistrationSchema, db: Session = Depends(get_db)):
    try:
        # Store selected_sports as JSON string
        reg_obj = event_registration_connector.create(db, {
            'first_name': request.first_name,
            'last_name': request.last_name,
            'email': request.email,
            'phone': request.phone,
            'selected_sports': json.dumps(request.selected_sports),
            'pickleball_level': request.pickleball_level
        })
        return {"id": reg_obj.id, "message": "Registration successful"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post('/transaction')
def create_transaction(request: TransactionSchema, db: Session = Depends(get_db)):
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