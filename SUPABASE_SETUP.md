# Supabase Integration Setup Guide

## Overview
TradeWise now includes Supabase integration for user authentication and data persistence. Users can:
- Register and login to save their scan results
- Store Fyers authentication tokens securely
- Access scan history and latest results
- Continue using the app without login (results won't be saved)

## Setup Instructions

### 1. Database Setup

Run the SQL schema in your Supabase dashboard:

1. Go to https://cxbcpmouqkajlxzmbomu.supabase.co
2. Navigate to SQL Editor
3. Copy the contents of `database/schema.sql`
4. Execute the SQL script

This will create:
- `users` table - User profiles
- `fyers_tokens` table - Fyers API tokens
- `screener_results` table - Individual stock signals
- `screener_scans` table - Scan session metadata

### 2. Environment Configuration

The Supabase credentials are already configured in `config/supabase_config.py`:
- **URL**: https://cxbcpmouqkajlxzmbomu.supabase.co
- **Anon Key**: (already set - safe for browser use with RLS enabled)

### 3. Install Dependencies

The Supabase Python client has been installed:
```bash
pip install supabase
```

### 4. Row Level Security (RLS)

The database schema includes RLS policies that ensure:
- Users can only access their own data
- All tables are protected
- Authenticated requests are required

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2026-01-18T..."
  },
  "expires_at": "2026-01-19T..."
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

#### Get Current User
```http
GET /api/auth/me?authorization=Bearer <token>
```

#### Logout
```http
POST /api/auth/logout?authorization=Bearer <token>
```

### Fyers Token Management

#### Store Fyers Token
```http
POST /api/fyers/token?authorization=Bearer <token>
Content-Type: application/json

{
  "access_token": "fyers_token",
  "refresh_token": "refresh_token",
  "expires_at": "2026-01-19T..."
}
```

#### Get Stored Token
```http
GET /api/fyers/token?authorization=Bearer <token>
```

#### Delete Token
```http
DELETE /api/fyers/token?authorization=Bearer <token>
```

### Screener with Persistence

#### Scan Stocks (with optional save)
```http
GET /screener/scan?limit=50&min_confidence=60&authorization=Bearer <token>
```

If `authorization` header is provided, results are automatically saved to database.

Response includes:
```json
{
  "status": "success",
  "saved": true,
  "scan_id": "uuid",
  "signals": {...},
  ...
}
```

#### Get Latest Scan
```http
GET /screener/latest?authorization=Bearer <token>
```

#### Get Scan History
```http
GET /screener/history?authorization=Bearer <token>&limit=10
```

## Frontend Usage

### Login Page
Access at: `http://localhost:8000/login.html`

Features:
- Login/Register tabs
- Form validation
- Token storage in localStorage
- Auto-redirect to screener after login

### Screener Page
Access at: `http://localhost:8000/screener.html`

Features:
- Shows user email when logged in
- Logout button
- Auto-saves scan results if authenticated
- Works without login (no persistence)
- Console messages indicate save status

### Authentication Flow

1. **User visits screener without login**:
   - Can use all features
   - Results are not saved
   - "Login" button visible

2. **User clicks Login**:
   - Redirected to `/login.html`
   - Can login or register
   - Token stored in localStorage

3. **User returns to screener**:
   - Automatically detected as logged in
   - Email shown in header
   - Scans auto-saved to database
   - Can view scan history

4. **User clicks Logout**:
   - Token removed
   - Page reloads
   - Back to guest mode

## Data Storage

### Scan Results
Each scan creates:
1. **Scan metadata** in `screener_scans`:
   - Scan ID
   - Timestamp
   - Stocks scanned count
   - Signal counts (BUY/SELL)
   - Scan parameters

2. **Individual signals** in `screener_results`:
   - Stock symbol, name, price
   - Action (BUY/SELL)
   - Confidence level
   - Targets and stop loss
   - Technical indicators
   - Reasons for signal

### Query Examples

Get user's latest scan:
```sql
SELECT * FROM screener_scans 
WHERE user_id = 'user-uuid' 
ORDER BY scan_time DESC 
LIMIT 1;
```

Get all BUY signals from latest scan:
```sql
SELECT * FROM screener_results 
WHERE user_id = 'user-uuid' 
AND scan_id = 'scan-uuid'
AND action = 'BUY'
ORDER BY confidence DESC;
```

## Security Features

1. **Row Level Security**: All tables have RLS enabled
2. **User Isolation**: Users can only access their own data
3. **Token Storage**: Fyers tokens encrypted in database
4. **Password Hashing**: Handled by Supabase Auth
5. **No Sensitive Data in Client**: Only anon key exposed (safe with RLS)

## Testing

### Test Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Test Scan with Save
```bash
# Get token from login response first
TOKEN="eyJhbGci..."

curl "http://localhost:8000/screener/scan?limit=10&min_confidence=60&authorization=Bearer%20$TOKEN"
```

### Test Get Latest Scan
```bash
curl "http://localhost:8000/screener/latest?authorization=Bearer%20$TOKEN"
```

## Troubleshooting

### Issue: Registration fails
- Check Supabase dashboard for error logs
- Verify email doesn't already exist
- Ensure password is at least 6 characters

### Issue: Scan results not saving
- Check browser console for errors
- Verify token is valid
- Check Supabase logs for RLS policy violations

### Issue: Cannot access saved scans
- Verify user is logged in
- Check token expiration
- Ensure RLS policies are created

## Next Steps

1. ✅ Database schema created
2. ✅ Authentication endpoints added
3. ✅ Fyers token storage implemented
4. ✅ Screener persistence added
5. ✅ Login UI created
6. ✅ Screener UI updated with auth
7. 🔄 Run SQL schema in Supabase
8. 🔄 Test registration and login
9. 🔄 Test scan saving
10. 🔄 Verify data in Supabase dashboard

## Production Checklist

- [ ] Run database schema in Supabase
- [ ] Test all auth endpoints
- [ ] Verify RLS policies working
- [ ] Test scan persistence
- [ ] Update API_BASE in frontend for production
- [ ] Enable HTTPS for production
- [ ] Review and update CORS settings
- [ ] Set up email confirmation (optional)
- [ ] Configure session timeout
- [ ] Add rate limiting
