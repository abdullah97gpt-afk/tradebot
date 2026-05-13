-- ============================================================
-- XAUUSD AI Trading Signal Platform - Supabase Schema
-- ============================================================
-- Run this entire file in Supabase SQL Editor (Project > SQL Editor)
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: signals
-- ============================================================
CREATE TABLE IF NOT EXISTS public.signals (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol        TEXT NOT NULL DEFAULT 'XAUUSD',
    mode          TEXT NOT NULL DEFAULT 'SCALPING',
    signal        TEXT NOT NULL CHECK (signal IN ('BUY', 'SELL', 'WAIT')),
    confidence    INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    entry         NUMERIC(12, 4),
    stop_loss     NUMERIC(12, 4),
    take_profit   NUMERIC(12, 4),
    risk_reward   NUMERIC(6, 2),
    trend         TEXT CHECK (trend IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    volatility    TEXT CHECK (volatility IN ('LOW', 'MEDIUM', 'HIGH')),
    news_impact   TEXT CHECK (news_impact IN ('LOW', 'MEDIUM', 'HIGH')),
    reasons       JSONB DEFAULT '[]'::JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: market_data
-- ============================================================
CREATE TABLE IF NOT EXISTS public.market_data (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol      TEXT NOT NULL DEFAULT 'XAUUSD',
    timeframe   TEXT NOT NULL DEFAULT 'M5',
    open        NUMERIC(12, 4) NOT NULL,
    high        NUMERIC(12, 4) NOT NULL,
    low         NUMERIC(12, 4) NOT NULL,
    close       NUMERIC(12, 4) NOT NULL,
    volume      NUMERIC(18, 2) DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: logs
-- ============================================================
CREATE TABLE IF NOT EXISTS public.logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level       TEXT NOT NULL DEFAULT 'INFO' CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message     TEXT NOT NULL,
    context     JSONB DEFAULT '{}'::JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: settings
-- ============================================================
CREATE TABLE IF NOT EXISTS public.settings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key         TEXT NOT NULL UNIQUE,
    value       JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_signals_created_at  ON public.signals (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol       ON public.signals (symbol);
CREATE INDEX IF NOT EXISTS idx_signals_signal       ON public.signals (signal);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol    ON public.market_data (symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timeframe ON public.market_data (timeframe);
CREATE INDEX IF NOT EXISTS idx_market_data_created  ON public.market_data (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_created_at       ON public.logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level            ON public.logs (level);

-- ============================================================
-- AUTO-UPDATE updated_at FOR settings
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER settings_updated_at
    BEFORE UPDATE ON public.settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE public.signals     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.market_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.logs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings    ENABLE ROW LEVEL SECURITY;

-- Public read-only access for signals (frontend uses anon key)
CREATE POLICY "signals_anon_select"
    ON public.signals FOR SELECT
    TO anon, authenticated
    USING (true);

-- Public read-only access for settings
CREATE POLICY "settings_anon_select"
    ON public.settings FOR SELECT
    TO anon, authenticated
    USING (true);

-- Service role has full access (AI engine uses service role key)
CREATE POLICY "signals_service_all"
    ON public.signals FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "market_data_service_all"
    ON public.market_data FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "logs_service_all"
    ON public.logs FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "settings_service_all"
    ON public.settings FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

-- ============================================================
-- REALTIME PUBLICATION
-- ============================================================
-- Enable realtime for signals table so frontend receives live updates
ALTER PUBLICATION supabase_realtime ADD TABLE public.signals;

-- ============================================================
-- DEFAULT SETTINGS
-- ============================================================
INSERT INTO public.settings (key, value) VALUES
    ('engine_mode',        '"SCALPING"'),
    ('min_confidence',     '65'),
    ('min_risk_reward',    '2.0'),
    ('atr_multiplier_sl',  '1.5'),
    ('atr_multiplier_tp',  '3.0'),
    ('news_filter_enabled', 'true'),
    ('version',            '"1.0.0"')
ON CONFLICT (key) DO NOTHING;
