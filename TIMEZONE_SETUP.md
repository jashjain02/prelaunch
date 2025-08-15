# Indian Standard Time (IST) Configuration

This application is configured to store and display all timestamps in Indian Standard Time (IST/UTC+5:30).

## Configuration Details

### Database Level
- **Timezone**: Set to `Asia/Kolkata` (IST/UTC+5:30)
- **Connection**: Automatically sets timezone on each database connection
- **Storage**: All timestamp columns store data in IST timezone

### Application Level
- **Models**: All datetime fields use IST timezone by default
- **API Responses**: Timestamps are formatted with "IST" suffix
- **Validation**: Consistent timezone handling across the application

## Files Modified

### Database Configuration
- `backend/db/database.py` - Added IST timezone configuration
- `backend/utils/timezone_utils.py` - Timezone utility functions

### Models Updated
- `backend/models/user_registration_model.py` - IST timezone for timestamps
- `backend/models/event_registration_model.py` - IST timezone for timestamps  
- `backend/models/transaction_model.py` - IST timezone for timestamps

### API Updates
- `backend/main.py` - IST timezone formatting in responses

## Migration

To apply IST timezone to existing databases:

```bash
cd backend
python migrations/set_timezone.py
```

This script will:
1. Set database timezone to `Asia/Kolkata`
2. Update existing timestamp data to IST (if needed)
3. Verify the configuration

## Timezone Utility Functions

```python
from utils.timezone_utils import (
    get_current_ist_time,
    convert_to_ist,
    format_ist_datetime,
    parse_ist_datetime
)

# Get current IST time
current_time = get_current_ist_time()

# Convert any datetime to IST
ist_time = convert_to_ist(some_datetime)

# Format datetime for display
formatted = format_ist_datetime(datetime_obj)

# Parse datetime string to IST
parsed = parse_ist_datetime("2024-01-01 12:00:00")
```

## Database Schema

All timestamp columns are defined as:
```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

## API Response Format

Timestamps in API responses are formatted as:
```
"2024-01-01 12:00:00 IST"
```

## Benefits

1. **Consistency**: All timestamps are in the same timezone
2. **Localization**: Appropriate for Indian users
3. **Clarity**: Explicit timezone indication in responses
4. **Maintainability**: Centralized timezone handling

## Notes

- The application assumes all user interactions are in IST
- Database connections automatically set timezone on connection
- Existing data may need migration if stored in different timezone
- All new records will automatically use IST timezone
