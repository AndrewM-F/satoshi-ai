# Supabase Setup

This directory contains Supabase configuration and migrations for the project.

## Setup

1. **Create a new Supabase project**

   - Go to [Supabase](https://supabase.com) and create a new project
   - Note down your project URL and API keys

2. **Configure environment variables**
   - Copy `.env.example` to `.env` in the project root
   - Update the values with your Supabase credentials

## Database Setup

### Initial Setup

1. Create the migrations table by running this SQL in the Supabase SQL Editor:

   ```sql
   CREATE TABLE IF NOT EXISTS public.schema_migrations (
       version BIGINT PRIMARY KEY,
       name TEXT NOT NULL,
       applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   GRANT ALL PRIVILEGES ON public.schema_migrations TO postgres;
   ```

2. Run the initial migration to set up authentication:

   ```sql
   -- Enable Row Level Security on all tables by default
   ALTER TABLE public.test_table ENABLE ROW LEVEL SECURITY;

   -- Create a profiles table to store additional user data
   CREATE TABLE IF NOT EXISTS public.profiles (
       id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
       username TEXT UNIQUE NOT NULL,
       full_name TEXT,
       avatar_url TEXT,
       website TEXT,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

## Running Migrations

Row Level Security is enabled on all tables. The following policies are in place:

- Users can view and update their own profile
- Additional policies can be added as needed

## Local Development

For local development, you can use Supabase CLI:

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Start local development environment
supabase start
```

## Deployment

Migrations can be applied to production using the Supabase Dashboard or CLI:

```bash
# Apply migrations to production
supabase db push
```

## Backups

Regular database backups should be configured through the Supabase Dashboard.

## Monitoring

Monitor your Supabase project through the Supabase Dashboard:

- Database performance
- API usage
- Authentication logs
- Storage usage
