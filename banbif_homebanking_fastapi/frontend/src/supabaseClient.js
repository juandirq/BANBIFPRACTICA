import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  import.meta.env.VITE_SUPABASE_KEY;

export const supabaseReady = Boolean(supabaseUrl && supabaseKey);

if (!supabaseReady) {
  console.error(
    "Faltan variables de Supabase. Revisa frontend/.env.local: VITE_SUPABASE_URL y VITE_SUPABASE_PUBLISHABLE_KEY"
  );
}

export const supabase = supabaseReady
  ? createClient(supabaseUrl, supabaseKey)
  : null;
