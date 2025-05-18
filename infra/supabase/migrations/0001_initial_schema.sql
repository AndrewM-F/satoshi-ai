-- ===========================================
-- Idempotent Schema Setup
-- Safe to run multiple times
-- ===========================================

-- Create required schemas if they do not exist
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS realtime;

-- Stub auth.users table for local/CI (safe if real table already exists)
CREATE TABLE IF NOT EXISTS auth.users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid()
    -- Add more columns if your migrations reference them
);

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing types if they exist (and all dependent objects)
DROP TYPE IF EXISTS content_status CASCADE;
DROP TYPE IF EXISTS meeting_status CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;

-- Recreate types
CREATE TYPE user_role AS ENUM ('admin', 'editor', 'viewer');
CREATE TYPE meeting_status AS ENUM ('scheduled', 'in_progress', 'completed', 'processed');
CREATE TYPE content_status AS ENUM ('draft', 'pending_review', 'approved', 'published', 'rejected');

-- ===========================================
-- Profiles Table
-- ===========================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role user_role NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add any missing columns to profiles
DO $$
BEGIN
    -- Add role column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_schema = 'public' 
                  AND table_name = 'profiles' 
                  AND column_name = 'role') THEN
        ALTER TABLE public.profiles ADD COLUMN role user_role NOT NULL DEFAULT 'viewer';
    END IF;
    
    -- Add other columns as needed...
END $$;

-- ===========================================
-- Discord Servers
-- ===========================================
CREATE TABLE IF NOT EXISTS public.discord_servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    owner_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- Discord Channels
-- ===========================================
CREATE TABLE IF NOT EXISTS public.discord_channels (
    id TEXT PRIMARY KEY,
    server_id TEXT REFERENCES public.discord_servers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    topic TEXT,
    position INTEGER,
    is_nsfw BOOLEAN DEFAULT false,
    parent_id TEXT,
    is_private BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(id, server_id)
);

-- ===========================================
-- Discord Messages
-- ===========================================
CREATE TABLE IF NOT EXISTS public.discord_messages (
    id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    server_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    content TEXT,
    is_bot BOOLEAN DEFAULT false,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, channel_id),
    FOREIGN KEY (channel_id, server_id) REFERENCES public.discord_channels(id, server_id) ON DELETE CASCADE
);

-- ===========================================
-- Meetings
-- ===========================================
CREATE TABLE IF NOT EXISTS public.meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    status meeting_status DEFAULT 'scheduled',
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    organizer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    discord_channel_id TEXT,
    discord_message_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (discord_message_id, discord_channel_id) 
        REFERENCES public.discord_messages(id, channel_id) ON DELETE SET NULL
);

-- ===========================================
-- Meeting Participants
-- ===========================================
CREATE TABLE IF NOT EXISTS public.meeting_participants (
    meeting_id UUID REFERENCES public.meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    is_organizer BOOLEAN DEFAULT false,
    attended BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (meeting_id, user_id)
);

-- ===========================================
-- Meeting Notes
-- ===========================================
CREATE TABLE IF NOT EXISTS public.meeting_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES public.meetings(id) ON DELETE CASCADE,
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- Content Items
-- ===========================================
CREATE TABLE IF NOT EXISTS public.content_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT,
    excerpt TEXT,
    status content_status DEFAULT 'draft',
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    meeting_id UUID REFERENCES public.meetings(id) ON DELETE SET NULL,
    discord_message_id TEXT,
    discord_channel_id TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (discord_channel_id, discord_message_id) 
        REFERENCES public.discord_messages(channel_id, id) ON DELETE SET NULL
);

-- ===========================================
-- Content Revisions
-- ===========================================
CREATE TABLE IF NOT EXISTS public.content_revisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES public.content_items(id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    excerpt TEXT,
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(content_id, revision_number)
);

-- ===========================================
-- Tags
-- ===========================================
CREATE TABLE IF NOT EXISTS public.tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- Content Tags
-- ===========================================
CREATE TABLE IF NOT EXISTS public.content_tags (
    content_id UUID REFERENCES public.content_items(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES public.tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (content_id, tag_id)
);

-- ===========================================
-- Comments
-- ===========================================
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    content_id UUID REFERENCES public.content_items(id) ON DELETE CASCADE,
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    parent_id UUID REFERENCES public.comments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- Media
-- ===========================================
CREATE TABLE IF NOT EXISTS public.media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    alt_text TEXT,
    uploader_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- Content Media
-- ===========================================
CREATE TABLE IF NOT EXISTS public.content_media (
    content_id UUID REFERENCES public.content_items(id) ON DELETE CASCADE,
    media_id UUID REFERENCES public.media(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (content_id, media_id)
);

-- RLS will be enabled in the security policies migration
