/**
 * Supabase client initialisation and data access layer for the frontend.
 * Uses the public anon key — read-only access enforced by RLS policies.
 */

import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";

let _client = null;

export function getSupabaseClient() {
  if (!_client) {
    _client = createClient(APP_CONFIG.supabase.url, APP_CONFIG.supabase.anonKey);
  }
  return _client;
}

/**
 * Fetch the most recent N signals, newest first.
 * @param {number} limit
 * @returns {Promise<Array>}
 */
export async function fetchLatestSignals(limit = APP_CONFIG.app.historyLimit) {
  const sb = getSupabaseClient();
  const { data, error } = await sb
    .from("signals")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("[supabase] fetchLatestSignals error:", error.message);
    return [];
  }
  return data ?? [];
}

/**
 * Subscribe to real-time inserts on the signals table.
 * @param {(signal: Object) => void} onNewSignal  callback receives new row
 * @returns {RealtimeChannel}  call .unsubscribe() to clean up
 */
export function subscribeToSignals(onNewSignal) {
  const sb = getSupabaseClient();
  const channel = sb
    .channel("signals-live")
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "signals" },
      (payload) => {
        if (payload.new) onNewSignal(payload.new);
      }
    )
    .subscribe((status) => {
      console.log("[realtime] signals channel status:", status);
    });
  return channel;
}
