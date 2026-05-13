export const SUPABASE_CONFIG = {
  url: "https://gdwyzdmtipmomjzappam.supabase.co/rest/v1/",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdkd3l6ZG10aXBtb21qemFwcGFtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2OTQyODUsImV4cCI6MjA5NDI3MDI4NX0.JQHQhzj43dhXrKSv8y6TBoFbt7XXSHIQ6jUsVh6D6DA"
};

export function validateConfig() {
  if (!SUPABASE_CONFIG.url || !SUPABASE_CONFIG.anonKey) {
    console.error("[supabase] Missing Supabase frontend config.");
    return false;
  }
  return true;
}
