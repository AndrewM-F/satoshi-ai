import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

// This client is for client-side usage
export const supabase = createClientComponentClient();

// For server components and API routes, use createServerComponentClient or createRouteHandlerClient
