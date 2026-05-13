/**
 * Frontend configuration.
 * Replace the placeholder values with your actual Supabase project details.
 * ONLY the anon (public) key is used here — never the service role key.
 */

const APP_CONFIG = {
  supabase: {
    url:     "https://gdwyzdmtipmomjzappam.supabase.co",   // ← replace
    anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdkd3l6ZG10aXBtb21qemFwcGFtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2OTQyODUsImV4cCI6MjA5NDI3MDI4NX0.JQHQhzj43dhXrKSv8y6TBoFbt7XXSHIQ6jUsVh6D6DA",                // ← replace
  },
  app: {
    name:            "XAUUSD Signal",
    symbol:          "XAUUSD",
    refreshInterval: 5000,    // fallback polling ms (realtime is primary)
    historyLimit:    20,      // rows in signal history table
  },
};
