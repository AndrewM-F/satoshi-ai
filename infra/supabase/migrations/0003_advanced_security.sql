-- ===========================================
-- Advanced Security Features
-- ===========================================

-- 1. User Role Management
-- ======================

-- Set default role for new users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  -- If role is not already set in metadata, set default role to 'viewer'
  IF NEW.raw_user_meta_data->>'role' IS NULL THEN
    NEW.raw_user_meta_data := 
      COALESCE(NEW.raw_user_meta_data, '{}'::jsonb) || 
      jsonb_build_object('role', 'viewer');
  END IF;
  
  -- Ensure raw_app_meta_data exists
  IF NEW.raw_app_meta_data IS NULL THEN
    NEW.raw_app_meta_data := '{}'::jsonb;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to set default role on user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 2. Email Verification Requirements
-- =================================

-- Require verified email for sensitive operations on test_table
DROP POLICY IF EXISTS "Require verified email for sensitive operations" ON public.test_table;
CREATE POLICY "Require verified email for sensitive operations"
ON public.test_table
FOR UPDATE
USING (
  auth.uid() = user_id AND 
  (SELECT email_confirmed_at IS NOT NULL FROM auth.users WHERE id = auth.uid())
)
WITH CHECK (
  auth.uid() = user_id AND 
  (SELECT email_confirmed_at IS NOT NULL FROM auth.users WHERE id = auth.uid())
);

-- 3. Audit Logging
-- ===============

-- Create audit log table
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  action TEXT NOT NULL,
  table_name TEXT NOT NULL,
  record_id TEXT,
  old_data JSONB,
  new_data JSONB,
  ip_address TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on audit logs
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Only admins can view audit logs
DROP POLICY IF EXISTS "Admins can view audit logs" ON public.audit_logs;
CREATE POLICY "Admins can view audit logs" 
ON public.audit_logs
FOR SELECT
USING (
  public.is_admin()
);

-- Function to automatically log changes
CREATE OR REPLACE FUNCTION public.log_table_change()
RETURNS TRIGGER AS $$
DECLARE
  record_id TEXT;
  action_type TEXT;
BEGIN
  -- Determine action type
  IF TG_OP = 'INSERT' THEN
    action_type := 'INSERT';
    record_id := NEW.id::TEXT;
  ELSIF TG_OP = 'UPDATE' THEN
    action_type := 'UPDATE';
    record_id := NEW.id::TEXT;
  ELSIF TG_OP = 'DELETE' THEN
    action_type := 'DELETE';
    record_id := OLD.id::TEXT;
  END IF;

  -- Insert into audit log
  INSERT INTO public.audit_logs (
    user_id,
    action,
    table_name,
    record_id,
    old_data,
    new_data
  ) VALUES (
    auth.uid(),
    action_type,
    TG_TABLE_NAME,
    record_id,
    CASE WHEN TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN to_jsonb(OLD) ELSE NULL END,
    CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN to_jsonb(NEW) ELSE NULL END
  );

  -- For INSERT and UPDATE operations, return NEW
  -- For DELETE operations, return OLD
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply audit logging to test_table
DROP TRIGGER IF EXISTS audit_test_table_changes ON public.test_table;
CREATE TRIGGER audit_test_table_changes
  AFTER INSERT OR UPDATE OR DELETE ON public.test_table
  FOR EACH ROW EXECUTE PROCEDURE public.log_table_change();

-- 4. Rate Limiting Function
-- =======================

-- Create a function to check rate limits
CREATE OR REPLACE FUNCTION public.check_rate_limit(
  action_key TEXT,
  max_attempts INTEGER,
  window_seconds INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
  user_id UUID;
  recent_count INTEGER;
BEGIN
  -- Get current user ID
  user_id := auth.uid();
  
  -- If no authenticated user, use IP address (stored in a session variable)
  IF user_id IS NULL THEN
    RETURN TRUE; -- For now, only apply to authenticated users
  END IF;
  
  -- Check if user has exceeded the rate limit
  WITH recent_actions AS (
    SELECT created_at 
    FROM public.audit_logs
    WHERE 
      user_id = auth.uid() AND
      action = action_key AND
      created_at > NOW() - (window_seconds * INTERVAL '1 second')
    ORDER BY created_at DESC
    LIMIT max_attempts
  )
  SELECT COUNT(*) INTO recent_count FROM recent_actions;
  
  -- Return true if under the limit, false if over
  RETURN recent_count < max_attempts;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Grant necessary permissions
-- ============================

GRANT ALL PRIVILEGES ON public.audit_logs TO postgres, service_role;
GRANT ALL PRIVILEGES ON SEQUENCE public.audit_logs_id_seq TO postgres, service_role;
