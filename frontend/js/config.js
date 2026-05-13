window.APP_CONFIG = {
  supabase: {
    url: "https://gdwyzdmtipmomjzappam.supabase.co",
    anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdkd3l6ZG10aXBtb21qemFwcGFtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2OTQyODUsImV4cCI6MjA5NDI3MDI4NX0.JQHQhzj43dhXrKSv8y6TBoFbt7XXSHIQ6jUsVh6D6DA"
  },
  dashboard: {
    historyLimit: 20,
    realtimeChannel: "signals",
    refreshIntervalMs: 30000
  }
};

window.validateConfig = function () {
  const cfg = window.APP_CONFIG?.supabase;

  if (!cfg?.url || !cfg?.anonKey) {
    console.error("[supabase] Missing Supabase config.");
    return false;
  }

  console.log("[supabase] Config loaded.");
  return true;
};
