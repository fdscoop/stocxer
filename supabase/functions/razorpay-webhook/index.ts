// Supabase Edge Function for Razorpay Webhook
// Handles payment.captured, subscription.charged, etc.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from "https://deno.land/std@0.177.0/crypto/mod.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-razorpay-signature',
}

interface RazorpayEvent {
  event: string
  payload: {
    payment?: {
      entity: {
        id: string
        order_id: string
        amount: number
        currency: string
        status: string
        method: string
        email?: string
        contact?: string
        notes?: Record<string, string>
      }
    }
    subscription?: {
      entity: {
        id: string
        plan_id: string
        status: string
        customer_id?: string
        current_start?: number
        current_end?: number
      }
    }
  }
  created_at: number
}

async function verifyWebhookSignature(
  body: string,
  signature: string,
  secret: string
): Promise<boolean> {
  const encoder = new TextEncoder()
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  )
  
  const signatureBuffer = await crypto.subtle.sign(
    "HMAC",
    key,
    encoder.encode(body)
  )
  
  const expectedSignature = Array.from(new Uint8Array(signatureBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
  
  return expectedSignature === signature
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get environment variables
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const webhookSecret = Deno.env.get('RAZORPAY_WEBHOOK_SECRET')!

    // Verify webhook signature
    const signature = req.headers.get('x-razorpay-signature')
    const body = await req.text()

    if (!signature) {
      return new Response(
        JSON.stringify({ error: 'Missing signature' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const isValid = await verifyWebhookSignature(body, signature, webhookSecret)
    
    if (!isValid) {
      console.error('Invalid webhook signature')
      return new Response(
        JSON.stringify({ error: 'Invalid signature' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Parse event data
    const event: RazorpayEvent = JSON.parse(body)
    console.log('Razorpay webhook event:', event.event)

    // Create Supabase client
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Handle different event types
    switch (event.event) {
      case 'payment.captured': {
        const payment = event.payload.payment?.entity
        if (!payment) break

        const userId = payment.notes?.user_id
        const packId = payment.notes?.pack_id
        
        if (!userId) {
          console.error('No user_id in payment notes')
          break
        }

        // Get credit pack details
        const { data: pack } = await supabase
          .from('credit_packs')
          .select('*')
          .eq('id', packId)
          .single()

        if (!pack) {
          console.error('Credit pack not found:', packId)
          break
        }

        const creditsToAdd = Number(pack.credits) + Number(pack.bonus_credits)

        // Get current balance
        const { data: userCredits } = await supabase
          .from('user_credits')
          .select('*')
          .eq('user_id', userId)
          .single()

        const currentBalance = userCredits ? Number(userCredits.balance) : 0
        const newBalance = currentBalance + creditsToAdd

        // Update or insert user credits
        const { error: creditsError } = await supabase
          .from('user_credits')
          .upsert({
            user_id: userId,
            balance: newBalance,
            lifetime_purchased: (userCredits?.lifetime_purchased || 0) + creditsToAdd,
            last_topped_up: new Date().toISOString()
          }, {
            onConflict: 'user_id'
          })

        if (creditsError) {
          console.error('Error updating credits:', creditsError)
          break
        }

        // Log transaction
        await supabase
          .from('credit_transactions')
          .insert({
            user_id: userId,
            transaction_type: 'purchase',
            amount: creditsToAdd,
            balance_before: currentBalance,
            balance_after: newBalance,
            description: `Credit purchase: ${pack.name}`,
            razorpay_payment_id: payment.id,
            razorpay_order_id: payment.order_id
          })

        // Log payment history
        await supabase
          .from('payment_history')
          .insert({
            user_id: userId,
            payment_type: 'credits',
            amount_inr: payment.amount,
            razorpay_payment_id: payment.id,
            razorpay_order_id: payment.order_id,
            status: 'captured',
            payment_method: payment.method,
            metadata: { pack_id: packId, credits_added: creditsToAdd }
          })

        console.log(`✅ Credits added: ${creditsToAdd} for user ${userId}`)
        break
      }

      case 'payment.failed': {
        const payment = event.payload.payment?.entity
        if (!payment) break

        const userId = payment.notes?.user_id
        if (!userId) break

        // Log failed payment
        await supabase
          .from('payment_history')
          .insert({
            user_id: userId,
            payment_type: 'credits',
            amount_inr: payment.amount,
            razorpay_payment_id: payment.id,
            razorpay_order_id: payment.order_id,
            status: 'failed',
            failure_reason: 'Payment failed',
            metadata: payment.notes
          })

        console.log(`❌ Payment failed for user ${userId}`)
        break
      }

      case 'subscription.charged': {
        const subscription = event.payload.subscription?.entity
        if (!subscription) break

        // TODO: Handle subscription renewal
        // Update user_subscriptions table with new period
        console.log('Subscription charged:', subscription.id)
        break
      }

      case 'subscription.cancelled': {
        const subscription = event.payload.subscription?.entity
        if (!subscription) break

        // Update subscription status
        await supabase
          .from('user_subscriptions')
          .update({
            status: 'cancelled',
            cancelled_at: new Date().toISOString()
          })
          .eq('razorpay_subscription_id', subscription.id)

        console.log('Subscription cancelled:', subscription.id)
        break
      }

      default:
        console.log('Unhandled event type:', event.event)
    }

    return new Response(
      JSON.stringify({ success: true, event: event.event }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )

  } catch (error) {
    console.error('Webhook error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})
