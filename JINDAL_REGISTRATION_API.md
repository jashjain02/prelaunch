# Jindal Registration API

This API provides endpoints for managing Jindal registrations for the Alldays Pre-Launch Experience.

## Features

### 🎯 **Complete Registration Management**
- Create new Jindal registrations
- Retrieve all registrations (admin)
- Get specific registration details
- Update registration information
- Payment status management

### 📊 **Data Validation**
- Email format validation
- Phone number validation (10 digits)
- JGU Student ID validation
- Indian state validation
- Payment status validation

### 🔒 **Data Integrity**
- Unique email constraint
- Unique JGU Student ID constraint
- IST timezone timestamps
- Rate limiting protection

## Database Schema

### Jindal Registrations Table
```sql
CREATE TABLE jindal_registrations (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL,
    jgu_student_id VARCHAR(50) NOT NULL UNIQUE,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    selected_sports TEXT,  -- JSON string of selected sports
    pickle_level VARCHAR(50),  -- For padel skill level
    total_amount INTEGER NOT NULL DEFAULT 0,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    payment_proof VARCHAR(500),  -- File path/URL for payment proof
    agreed_to_terms BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### Create Jindal Registration
```http
POST /jindal-registration
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@jgu.ac.in",
  "phone": "9876543210",
  "jgu_student_id": "JGU2024001",
  "city": "Mumbai",
  "state": "Maharashtra",
  "selected_sports": ["padel"],
  "pickle_level": "Beginner",
  "total_amount": 200,
  "payment_status": "pending",
  "agreed_to_terms": true
}
```

**Response:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@jgu.ac.in",
  "phone": "9876543210",
  "jgu_student_id": "JGU2024001",
  "city": "Mumbai",
  "state": "Maharashtra",
  "selected_sports": ["padel"],
  "pickle_level": "Beginner",
  "total_amount": 200,
  "payment_status": "pending",
  "payment_proof": null,
  "agreed_to_terms": true,
  "created_at": "2024-01-15T10:30:00+05:30",
  "updated_at": "2024-01-15T10:30:00+05:30"
}
```

### Get All Registrations (Admin)
```http
GET /jindal-registrations
```

**Response:**
```json
{
  "total_registrations": 5,
  "registrations": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@jgu.ac.in",
      "phone": "9876543210",
      "jgu_student_id": "JGU2024001",
      "city": "Mumbai",
      "state": "Maharashtra",
      "selected_sports": ["padel"],
      "pickle_level": "Beginner",
      "total_amount": 200,
      "payment_status": "completed",
      "payment_proof": "uploads/payment_proof_1.jpg",
      "agreed_to_terms": true,
      "created_at": "2024-01-15T10:30:00+05:30",
      "updated_at": "2024-01-15T11:45:00+05:30"
    }
  ]
}
```

### Get Specific Registration
```http
GET /jindal-registration/{registration_id}
```

### Update Registration
```http
PUT /jindal-registration/{registration_id}
Content-Type: application/json

{
  "payment_status": "completed",
  "payment_proof": "uploads/payment_proof_1.jpg"
}
```

### Update Payment Status
```http
PUT /jindal-registration/{registration_id}/payment?payment_status=completed&payment_proof=uploads/proof.jpg
```

### Get Registrations Summary (Admin)
```http
GET /jindal-registrations-summary
```

**Response:**
```json
{
  "total_registrations": 25,
  "pending_payments": 5,
  "completed_payments": 18,
  "failed_payments": 2,
  "total_revenue": 3600
}
```

## Data Validation Rules

### Required Fields
- `first_name`: Minimum 2 characters
- `last_name`: Minimum 2 characters
- `email`: Valid email format, unique
- `phone`: Exactly 10 digits
- `jgu_student_id`: Minimum 3 characters, unique
- `city`: Non-empty string
- `state`: Must be valid Indian state
- `agreed_to_terms`: Must be true

### Optional Fields
- `selected_sports`: Array of sport keys
- `pickle_level`: "Beginner", "Intermediate", or "Advanced"
- `total_amount`: Non-negative integer
- `payment_status`: "pending", "completed", or "failed"
- `payment_proof`: File path/URL string

### Indian States
Valid states include all Indian states and union territories:
- Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh
- Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand
- Karnataka, Kerala, Madhya Pradesh, Maharashtra, Manipur
- Meghalaya, Mizoram, Nagaland, Odisha, Punjab
- Rajasthan, Sikkim, Tamil Nadu, Telangana, Tripura
- Uttar Pradesh, Uttarakhand, West Bengal
- Delhi, Jammu and Kashmir, Ladakh, Chandigarh
- Dadra and Nagar Haveli and Daman and Diu, Lakshadweep, Puducherry

## Error Handling

### Common Error Responses
- `400` - Validation error (invalid data, duplicate email/JGU ID)
- `404` - Registration not found
- `429` - Rate limit exceeded
- `500` - Server error

### Error Messages
- "Email already registered"
- "JGU Student ID already registered"
- "Phone number must be exactly 10 digits"
- "State must be one of: [valid states]"
- "Registration not found"

## Setup Instructions

### 1. Create Database Table
```bash
cd backend
python migrations/create_jindal_table.py
```

### 2. Test API Endpoints
```bash
# Create registration
curl -X POST http://localhost:8000/jindal-registration \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@jgu.ac.in",
    "phone": "9876543210",
    "jgu_student_id": "JGU2024001",
    "city": "Mumbai",
    "state": "Maharashtra",
    "selected_sports": ["padel"],
    "pickle_level": "Beginner",
    "total_amount": 200,
    "agreed_to_terms": true
  }'

# Get all registrations
curl http://localhost:8000/jindal-registrations

# Get summary
curl http://localhost:8000/jindal-registrations-summary
```

## Frontend Integration

### Create Registration
```javascript
const createJindalRegistration = async (registrationData) => {
  try {
    const response = await fetch('/api/jindal-registration', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(registrationData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error creating registration:', error);
    throw error;
  }
};
```

### Update Payment Status
```javascript
const updatePaymentStatus = async (registrationId, paymentStatus, paymentProof) => {
  try {
    const response = await fetch(`/api/jindal-registration/${registrationId}/payment?payment_status=${paymentStatus}&payment_proof=${paymentProof}`, {
      method: 'PUT'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error updating payment status:', error);
    throw error;
  }
};
```

## Benefits

1. **Complete Registration Flow** - End-to-end registration management
2. **Data Validation** - Comprehensive input validation
3. **Payment Tracking** - Payment status and proof management
4. **Admin Dashboard** - Summary and detailed views
5. **IST Timezone** - All timestamps in Indian Standard Time
6. **Rate Limiting** - Protection against abuse
7. **Error Handling** - Comprehensive error responses
8. **Scalable** - Easy to extend with additional fields

## Monitoring

### Logs
All registration operations are logged:
```
INFO: Created Jindal registration for John Doe
INFO: Updated payment status for registration 1 to completed
```

### Metrics
Track via `/jindal-registrations-summary`:
- Total registrations
- Payment status breakdown
- Total revenue
- Registration trends

This API provides a complete solution for managing Jindal registrations with proper validation, error handling, and admin capabilities.
