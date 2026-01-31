"""Create ai_chat_history table in Supabase"""
from config.supabase_config import get_supabase_admin_client

supabase = get_supabase_admin_client()

# Test inserting with minimal data - if table doesn't exist, this will tell us
try:
    # Try to query the table first
    result = supabase.table('ai_chat_history').select('id').limit(1).execute()
    print('Table exists! Found', len(result.data), 'records')
except Exception as e:
    print(f'Table does not exist or error: {e}')
    print('\nPlease create the table manually in Supabase SQL Editor:')
    print('''
CREATE TABLE IF NOT EXISTS public.ai_chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    scan_id UUID,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    citations JSONB,
    tokens_used INTEGER DEFAULT 0,
    cached BOOLEAN DEFAULT FALSE,
    confidence_score FLOAT,
    query_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add RLS
ALTER TABLE public.ai_chat_history ENABLE ROW LEVEL SECURITY;

-- Policy for service role to insert (bypass RLS for admin operations)
CREATE POLICY "Service role full access" ON public.ai_chat_history
    FOR ALL USING (true) WITH CHECK (true);
''')
