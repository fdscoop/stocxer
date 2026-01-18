# AUTH FIX GUIDE - Login Issues Resolved

## Problem
After successful account creation, login shows "Invalid credentials" error because:
1. Email confirmation is required but the confirmation link points to wrong URL (localhost:3000)
2. Users cannot login until they confirm their email

## Solution

### Step 1: Update Supabase Settings (REQUIRED)

Go to your Supabase Dashboard and make these changes:

**URL:** https://supabase.com/dashboard/project/cxbcpmouqkajlxzmbomu/auth/providers

#### 1.1 Disable Email Confirmation (for Development)
- Navigate to: **Authentication → Providers → Email**
- Find **"Confirm email"** toggle
- **DISABLE IT** (turn it OFF)
- Click **Save**

#### 1.2 Update Redirect URLs
- Navigate to: **Authentication → URL Configuration**
- Under **"Redirect URLs"**, add:
  ```
  http://localhost:8000/*
  http://localhost:8000/callback
  ```
- Under **"Site URL"**, set:
  ```
  http://localhost:8000
  ```
- Click **Save**

### Step 2: Confirm Existing Unconfirmed Users

If you already have users who registered but can't login, run this SQL:

**URL:** https://supabase.com/dashboard/project/cxbcpmouqkajlxzmbomu/sql

```sql
UPDATE auth.users
SET email_confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;
```

This will immediately confirm all existing unconfirmed users so they can login.

### Step 3: Restart Your Application

```bash
# Stop old processes
pkill -9 -f "python main.py"
lsof -i :8000 | tail -n +2 | awk '{print $2}' | xargs kill -9

# Start fresh
cd /Users/bineshbalan/TradeWise
source venv/bin/activate
python main.py
```

## Testing

### Test Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"testuser@example.com",
    "password":"securepassword123",
    "full_name":"Test User"
  }'
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"testuser@example.com",
    "password":"securepassword123"
  }'
```

You should now get an access token immediately!

## What Changed

### Code Changes Made:
1. ✅ Updated `auth_service.py` to provide better error messages
2. ✅ Added SQL script to confirm users in `schema.sql`
3. ✅ Created `fix_unconfirmed_users.py` helper script

### Supabase Changes Needed:
1. ⚠️ **DISABLE email confirmation** (you must do this manually)
2. ⚠️ **Update redirect URLs** (you must do this manually)
3. ⚠️ **Confirm existing users with SQL** (optional, only if users already exist)

## Production Considerations

For production deployment, you should:
1. **Re-enable email confirmation** for security
2. **Set proper redirect URLs** for your production domain
3. **Configure SMTP settings** for reliable email delivery
4. **Add password reset flow**
5. **Implement email verification UI**

## Troubleshooting

### Still Getting "Invalid credentials"?
- Check that you disabled email confirmation in Supabase
- Verify the email/password are correct
- Run the SQL query to confirm existing users
- Check server logs for detailed error messages

### Users showing "Email not confirmed"?
- You didn't disable email confirmation in Supabase
- Run the SQL query to confirm them manually

### Still stuck?
- Check browser console for detailed errors
- Check server logs: `tail -f /tmp/tradewise.log`
- Verify Supabase settings are saved correctly
