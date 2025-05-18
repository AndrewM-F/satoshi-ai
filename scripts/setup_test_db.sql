-- Script to set up the test environment for Supabase integration tests
-- This sets up a minimal test table with RLS policies for testing

-- Drop the table if it already exists
DROP TABLE IF EXISTS public.test_table CASCADE;

-- Create the test table with all required fields
CREATE TABLE public.test_table (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    value INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id)
);

-- Add comments for documentation
COMMENT ON TABLE public.test_table IS 'Test table for Supabase integration tests';
COMMENT ON COLUMN public.test_table.user_id IS 'Reference to the user who owns this record';

-- Create indexes for better query performance
CREATE INDEX idx_test_table_is_active ON public.test_table (is_active);
CREATE INDEX idx_test_table_user_id ON public.test_table (user_id);

-- Enable Row Level Security
ALTER TABLE public.test_table ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- 0. Anonymous users can read all records (for test_anonymous_access)
DROP POLICY IF EXISTS "Anon can read" ON public.test_table;
CREATE POLICY "Anon can read"
ON public.test_table
FOR SELECT
TO anon
USING (true);

-- 1. Users can only read their own records
DROP POLICY IF EXISTS "Users can read own records" ON public.test_table;
CREATE POLICY "Users can read own records"
ON public.test_table
FOR SELECT
USING (auth.uid() = user_id);

-- 2. Only allow authenticated users to insert records
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON public.test_table;
CREATE POLICY "Enable insert for authenticated users"
ON public.test_table
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- 3. Users can only update their own records
DROP POLICY IF EXISTS "Users can update own records" ON public.test_table;
CREATE POLICY "Users can update own records"
ON public.test_table 
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 4. Users can only delete their own records
DROP POLICY IF EXISTS "Users can delete own records" ON public.test_table;
CREATE POLICY "Users can delete own records"
ON public.test_table
FOR DELETE
USING (auth.uid() = user_id);

-- 5. (Optional) Allow admins to do anything (for JWT-based admin users)
DROP POLICY IF EXISTS "Admins can do anything" ON public.test_table;
CREATE POLICY "Admins can do anything"
ON public.test_table
FOR ALL
USING (
  auth.role() = 'service_role'
  OR EXISTS (
    SELECT 1 FROM auth.users
    WHERE id = auth.uid()
    AND (raw_user_meta_data->>'role' = 'admin')
  )
);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON TABLE public.test_table TO postgres, anon, authenticated, service_role;
GRANT ALL PRIVILEGES ON SEQUENCE public.test_table_id_seq TO postgres, anon, authenticated, service_role;

-- Allow authenticated users to select from auth.users (needed for FK checks in tests)
GRANT SELECT ON TABLE auth.users TO authenticated;
