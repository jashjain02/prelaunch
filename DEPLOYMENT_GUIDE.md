# Deployment Guide: Orangetheory Event Update

## Overview
This guide outlines the steps to deploy the updated backend code that supports the new "Alldays x OnTour Run Club – Orangetheory Fitness Session" event.

## Changes Made

### 1. Database Model Updates
- **File**: `backend/models/event_registration_model.py`
- **Change**: Replaced `pickleball_level` column with `orangetheory_batch`
- **Purpose**: Store batch selection (batch1: 7:30-8:30 AM, batch2: 9:00-10:00 AM)

### 2. API Endpoint Updates
- **File**: `backend/main.py`
- **Changes**:
  - Updated `/event-registration` endpoint to accept `orangetheory_batch` instead of `pickleball_level`
  - Updated `/registrations` endpoint to return `orangetheory_batch` field
  - Updated `/registration-counts` endpoint to track "orangetheory" registrations
  - Set availability limit to 50 for Orangetheory event

### 3. Schema Updates
- **File**: `backend/schemas/event_registration_schema.py`
- **Change**: Updated field from `pickleball_level` to `orangetheory_batch`

## Production Deployment Steps

### Step 1: Database Migration
Run the migration script on the production database:

```sql
-- Execute the migration script: migration_orangetheory_update.sql
-- This will:
-- 1. Add orangetheory_batch column
-- 2. Migrate any existing data
-- 3. Drop the old pickleball_level column
-- 4. Create necessary indexes
```

### Step 2: Deploy Backend Code
1. Commit all changes to your repository
2. Deploy to Heroku:
   ```bash
   git add .
   git commit -m "Update backend for Orangetheory event"
   git push heroku main
   ```

### Step 3: Verify Deployment
1. Check the API is running: https://alldays-c9c62d7851d5.herokuapp.com/
2. Test the registration endpoint: https://alldays-c9c62d7851d5.herokuapp.com/event-registration
3. Check registrations: https://alldays-c9c62d7851d5.herokuapp.com/registrations
4. Check registration counts: https://alldays-c9c62d7851d5.herokuapp.com/registration-counts

## API Endpoints

### Event Registration
- **URL**: `POST /event-registration`
- **Parameters**:
  - `first_name` (required): User's first name
  - `last_name` (required): User's last name
  - `email` (required): User's email
  - `phone` (required): User's phone number
  - `selected_sports` (required): JSON string of selected sports (e.g., "[\"orangetheory\"]")
  - `orangetheory_batch` (optional): "batch1" or "batch2"
  - `event_date` (optional): Event date (default: "24th August 2025")
  - `event_location` (optional): Event location (default: "Orangetheory Fitness, Worli")
  - `file` (optional): Payment screenshot

### Get All Registrations
- **URL**: `GET /registrations`
- **Returns**: List of all registrations with enhanced fields:
  - `orangetheory_batch`: Batch selection
  - `event_date`: Event date
  - `event_location`: Event location
  - `payment_status`: Payment status
  - `is_active`: Active status
  - `created_at` & `updated_at`: Timestamps

### Get Registration Counts
- **URL**: `GET /registration-counts`
- **Returns**: Availability data for Orangetheory event

## Data Flow

1. **Frontend** sends registration data with `orangetheory_batch` field
2. **Backend** stores data in `event_registrations` table
3. **Database** stores batch selection as "batch1" or "batch2"
4. **API** returns registration confirmation with booking ID

## Monitoring

After deployment, monitor:
- Registration success rate
- Database performance
- API response times
- Error logs in Heroku

## Rollback Plan

If issues occur:
1. Revert to previous git commit
2. Restore database from backup
3. Redeploy previous version

## Contact

For deployment issues, check Heroku logs:
```bash
heroku logs --tail -a alldays-c9c62d7851d5
```
