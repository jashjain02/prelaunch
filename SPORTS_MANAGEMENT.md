# Sports Management System

This system provides real-time ticket management for sports events with automatic sold-out detection and capacity management.

## Features

### 🎯 **Automatic Sold-Out Management**
- Real-time ticket count tracking
- Automatic sold-out status when capacity is reached
- Prevents overbooking
- Frontend automatically blocks sold-out sports

### 📊 **Capacity Management**
- Set maximum capacity for each sport
- Track current ticket count
- Calculate remaining tickets
- Update capacity dynamically

### 🔄 **Real-Time Updates**
- Instant availability status updates
- Live ticket count monitoring
- Automatic status changes

## Database Schema

### Sports Table
```sql
CREATE TABLE sports (
    id SERIAL PRIMARY KEY,
    sport_name VARCHAR(100) NOT NULL UNIQUE,
    sport_key VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    price INTEGER NOT NULL DEFAULT 0,
    max_capacity INTEGER NOT NULL DEFAULT 50,
    current_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_sold_out BOOLEAN NOT NULL DEFAULT FALSE,
    timing VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### Get All Sports
```http
GET /sports
```
**Response:**
```json
{
  "total_sports": 3,
  "available_sports": 2,
  "sold_out_sports": 1,
  "sports": [
    {
      "sport_key": "padel",
      "sport_name": "Padel",
      "price": 200,
      "current_count": 0,
      "max_capacity": 0,
      "remaining_tickets": 0,
      "is_available": false,
      "is_sold_out": true,
      "timing": "4-8pm"
    }
  ]
}
```

### Get Specific Sport
```http
GET /sports/{sport_key}
```

### Purchase Tickets
```http
POST /sports/{sport_key}/purchase
Content-Type: application/json

{
  "quantity": 2
}
```

### Create New Sport (Admin)
```http
POST /sports
Content-Type: application/json

{
  "sport_name": "New Sport",
  "sport_key": "new_sport",
  "description": "Description",
  "price": 150,
  "max_capacity": 30,
  "timing": "5-7pm"
}
```

### Refund Tickets (Admin)
```http
POST /sports/{sport_key}/refund?quantity=1
```

### Reset Sport Count (Admin)
```http
POST /sports/{sport_key}/reset
```

### Get Sports Summary (Admin)
```http
GET /sports-summary
```

## Model Methods

### SportsModel Properties
- `remaining_tickets` - Calculate remaining tickets
- `is_available` - Check if sport is available for booking

### SportsModel Methods
- `increment_count(quantity)` - Purchase tickets
- `decrement_count(quantity)` - Refund tickets
- `reset_count()` - Reset to 0
- `set_capacity(new_capacity)` - Update capacity

## Setup Instructions

### 1. Initialize Sports Table
```bash
cd backend
python scripts/init_sports.py
```

### 2. Set Timezone (if not done)
```bash
python migrations/set_timezone.py
```

### 3. Default Sports Configuration
The system comes with these default sports:

| Sport | Key | Price | Capacity | Status |
|-------|-----|-------|----------|--------|
| Padel | padel | ₹200 | 0 | 🔴 Sold Out |

## Frontend Integration

### Update Sports.jsx
Replace the static sports array with API call:

```javascript
const [sports, setSports] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetchSports();
}, []);

const fetchSports = async () => {
  try {
    const response = await fetch('/api/sports');
    const data = await response.json();
    setSports(data.sports);
  } catch (error) {
    console.error('Error fetching sports:', error);
  } finally {
    setLoading(false);
  }
};
```

### Disable Sold-Out Sports
```javascript
const isSportAvailable = (sport) => {
  return sport.is_available && !sport.is_sold_out;
};

// In your JSX
{!isSportAvailable(sport) && (
  <div className="sold-out-overlay">
    <span>SOLD OUT</span>
  </div>
)}
```

## Admin Functions

### Update Sport Capacity
```python
from scripts.init_sports import update_sport_capacity

# Make padel available with 30 tickets
update_sport_capacity("padel", 30)
```

### Monitor Sales
```bash
curl http://localhost:8000/sports-summary
```

### Reset Counts
```bash
curl -X POST http://localhost:8000/sports/padel/reset
```

## Error Handling

### Common Error Responses
- `400` - Invalid request (insufficient tickets, sport not found)
- `404` - Sport not found
- `429` - Rate limit exceeded
- `500` - Server error

### Error Messages
- "Sport 'padel' is sold out"
- "Only 5 tickets remaining for Padel"
- "Sport 'invalid_sport' not found"

## Benefits

1. **Real-Time Management** - Instant updates across all clients
2. **Prevent Overbooking** - Automatic capacity enforcement
3. **Admin Control** - Easy capacity and count management
4. **Scalable** - Add new sports easily
5. **Audit Trail** - Track all changes with timestamps
6. **IST Timezone** - All timestamps in Indian Standard Time

## Monitoring

### Logs
All ticket operations are logged:
```
INFO: Purchased 2 tickets for Padel. New count: 15
INFO: Refunded 1 tickets for Padel. New count: 14
INFO: Reset ticket count for Padel
```

### Metrics
Track via `/sports-summary`:
- Total sports
- Available sports
- Sold out sports
- Total tickets sold
- Total capacity

This system ensures no overbooking while providing real-time availability status to users.
