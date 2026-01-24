#!/bin/bash

# Billing System Setup Script
# Run this after creating the billing tables in Supabase

echo "🚀 Setting up Hybrid Subscription + PAYG Billing System..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate || {
        echo "❌ Failed to activate virtual environment. Please run: source venv/bin/activate"
        exit 1
    }
fi

echo "✅ Virtual environment activated"
echo ""

# Install required packages
echo "📦 Installing Razorpay SDK..."
pip install razorpay>=1.4.1

echo ""
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please update .env with your Razorpay credentials:"
    echo "   - RAZORPAY_KEY_ID"
    echo "   - RAZORPAY_KEY_SECRET"
    echo "   - RAZORPAY_WEBHOOK_SECRET"
    echo ""
fi

echo "✅ Environment file ready"
echo ""

# Check if Supabase is configured
if grep -q "your_supabase_url_here" .env; then
    echo "⚠️  Supabase not configured in .env"
    echo "   Please update SUPABASE_URL and SUPABASE_KEY"
    echo ""
fi

echo "📋 Next Steps:"
echo ""
echo "1. Configure Razorpay:"
echo "   - Sign up at https://razorpay.com/"
echo "   - Get API keys from https://dashboard.razorpay.com/app/keys"
echo "   - Use test keys (rzp_test_*) for development"
echo "   - Add keys to .env file"
echo ""
echo "2. Run Database Migration:"
echo "   - Open Supabase SQL Editor"
echo "   - Copy contents of database/migrations/subscription_schema.sql"
echo "   - Execute in SQL Editor"
echo "   - Verify tables created successfully"
echo ""
echo "3. Configure Webhooks:"
echo "   - Go to Razorpay Dashboard → Settings → Webhooks"
echo "   - Add URL: https://your-domain.com/api/billing/webhooks/razorpay"
echo "   - Enable events: payment.captured, payment.failed, subscription.*"
echo "   - Copy webhook secret to .env"
echo ""
echo "4. Test the System:"
echo "   - Start the server: uvicorn main:app --reload"
echo "   - Visit /api/billing/status (requires login)"
echo "   - Try buying credits with test card: 4111 1111 1111 1111"
echo ""
echo "📖 Full documentation: BILLING_SYSTEM_GUIDE.md"
echo ""
echo "✨ Setup complete! Happy billing! ✨"
