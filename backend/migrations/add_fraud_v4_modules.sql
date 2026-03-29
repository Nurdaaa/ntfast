-- Migration: Add FraudEngine v4 module columns to analyses table
-- Date: 2026-03-07
-- Description: Adds 4 new antifraud module result columns:
--   - night_transactions_result (ночные транзакции)
--   - duplicate_payments_result (дублирующие платежи)
--   - round_amounts_result (круглые суммы)
--   - profile_mismatch_result (несоответствие профилю)

-- Add new fraud module columns (JSON, nullable)
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS night_transactions_result JSON;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS duplicate_payments_result JSON;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS round_amounts_result JSON;
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS profile_mismatch_result JSON;

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'analyses'
AND column_name IN (
    'night_transactions_result',
    'duplicate_payments_result',
    'round_amounts_result',
    'profile_mismatch_result'
)
ORDER BY column_name;
