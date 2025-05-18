-- ===========================================
-- Security Policies and Helper Functions
-- ===========================================

-- Stub auth.uid() for local/CI environments
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN gen_random_uuid();
END;
$$;

-- Stub auth.role() for local/CI environments
CREATE OR REPLACE FUNCTION auth.role() RETURNS text
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN 'authenticated';
END;
$$;

-- 1. Helper Functions
-- ===================

-- Check if current user is an admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM auth.users
        WHERE id = auth.uid() AND raw_user_meta_data->>'role' = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get current user's ID
CREATE OR REPLACE FUNCTION public.auth_uid()
RETURNS UUID AS $$
BEGIN
    RETURN auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if current user owns a record
CREATE OR REPLACE FUNCTION public.is_owner(table_name text, record_id anyelement)
RETURNS BOOLEAN AS $$
DECLARE
    owner_id UUID;
    result BOOLEAN;
BEGIN
    EXECUTE format('SELECT EXISTS (
        SELECT 1 FROM %I 
        WHERE id = $1 AND (
            user_id = $2 OR 
            created_by = $2 OR
            owner_id = $2
        )
    )', table_name)
    INTO result
    USING record_id, auth.uid();
    
    RETURN result;
EXCEPTION WHEN OTHERS THEN
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. RLS Policies for Profiles
-- ===========================

-- Enable RLS if not already enabled
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Users can view their own profile
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 3. RLS Policies for Discord Servers
-- =================================

-- Enable RLS
ALTER TABLE public.discord_servers ENABLE ROW LEVEL SECURITY;

-- Anyone can view servers
CREATE POLICY "Anyone can view servers"
    ON public.discord_servers FOR SELECT
    USING (true);

-- Only admins can insert/update/delete servers
CREATE POLICY "Only admins can manage servers"
    ON public.discord_servers FOR ALL
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- 4. RLS Policies for Discord Channels
-- ===================================

-- Enable RLS
ALTER TABLE public.discord_channels ENABLE ROW LEVEL SECURITY;

-- Anyone can view channels
CREATE POLICY "Anyone can view channels"
    ON public.discord_channels FOR SELECT
    USING (true);

-- Only admins can manage channels
CREATE POLICY "Only admins can manage channels"
    ON public.discord_channels FOR ALL
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

-- 5. RLS Policies for Meetings
-- ===========================

-- Enable RLS
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;

-- Users can view meetings they're participating in
CREATE POLICY "Users can view their meetings"
    ON public.meetings FOR SELECT
    USING (
        auth.role() = 'authenticated' AND (
            organizer_id = auth.uid() OR
            EXISTS (
                SELECT 1 FROM public.meeting_participants mp 
                WHERE mp.meeting_id = meetings.id AND mp.user_id = auth.uid()
            )
        )
    );

-- Organizers can manage their meetings
CREATE POLICY "Organizers can manage their meetings"
    ON public.meetings FOR ALL
    USING (organizer_id = auth.uid())
    WITH CHECK (organizer_id = auth.uid());

-- 6. RLS Policies for Content Items
-- ================================

-- Enable RLS
ALTER TABLE public.content_items ENABLE ROW LEVEL SECURITY;

-- Anyone can view published content
CREATE POLICY "Anyone can view published content"
    ON public.content_items FOR SELECT
    USING (status = 'published');

-- Authors can view their own content
CREATE POLICY "Authors can view their content"
    ON public.content_items FOR SELECT
    USING (author_id = auth.uid());

-- Authors can manage their content
CREATE POLICY "Authors can manage their content"
    ON public.content_items FOR ALL
    USING (author_id = auth.uid())
    WITH CHECK (author_id = auth.uid());

-- 7. RLS Policies for Comments
-- ===========================

-- Enable RLS
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;

-- Anyone can view comments
CREATE POLICY "Anyone can view comments"
    ON public.comments FOR SELECT
    USING (true);

-- Users can manage their own comments
CREATE POLICY "Users can manage their comments"
    ON public.comments FOR ALL
    USING (author_id = auth.uid())
    WITH CHECK (author_id = auth.uid());

-- 8. RLS Policies for Media
-- ========================

-- Enable RLS
ALTER TABLE public.media ENABLE ROW LEVEL SECURITY;

-- Users can view all media
CREATE POLICY "Users can view all media"
    ON public.media FOR SELECT
    USING (true);

-- Users can manage their own media
CREATE POLICY "Users can manage their media"
    ON public.media FOR ALL
    USING (uploader_id = auth.uid())
    WITH CHECK (uploader_id = auth.uid());

-- 9. Admin Override
-- ================

-- Allow admins to perform any operation on any table
CREATE OR REPLACE FUNCTION public.admin_override()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN public.is_admin();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply admin override and enable RLS on all tables
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT IN ('spatial_ref_sys')
    LOOP
        -- Enable RLS if not already enabled
        IF NOT EXISTS (
            SELECT 1 
            FROM pg_policies 
            WHERE tablename = t.tablename 
            AND schemaname = 'public'
        ) THEN
            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t.tablename);
            RAISE NOTICE 'Enabled RLS on %', t.tablename;
        END IF;
        
        -- Create admin policy if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 
            FROM pg_policies 
            WHERE tablename = t.tablename 
            AND schemaname = 'public'
            AND policyname = 'Admins have full access'
        ) THEN
            EXECUTE format('CREATE POLICY "Admins have full access" 
                ON %I FOR ALL 
                USING (public.admin_override()) 
                WITH CHECK (public.admin_override())', t.tablename);
            RAISE NOTICE 'Added admin policy to %', t.tablename;
        END IF;
    END LOOP;
END $$;
