-- Migration: Add unique_identifier to subjects table
-- Date: 2025-11-30
-- Description: Добавление поля unique_identifier для идентификации субъектов БЕЗ ИИН/БИН

-- Step 1: Add new column unique_identifier
ALTER TABLE subjects
ADD COLUMN IF NOT EXISTS unique_identifier VARCHAR(200);

-- Step 2: Make iin_bin nullable (drop NOT NULL constraint)
ALTER TABLE subjects
ALTER COLUMN iin_bin DROP NOT NULL;

-- Step 3: Generate unique_identifier for existing records
-- Для existing записей с iin_bin используем iin_bin как identifier
UPDATE subjects
SET unique_identifier = iin_bin
WHERE unique_identifier IS NULL AND iin_bin IS NOT NULL;

-- Для записей без iin_bin генерируем identifier из name + type
UPDATE subjects
SET unique_identifier = LOWER(REGEXP_REPLACE(name, '[^a-zA-Z0-9]', '_', 'g')) || '_' || type
WHERE unique_identifier IS NULL;

-- Step 4: Remove duplicates if any (keep the oldest record)
DELETE FROM subjects a
USING subjects b
WHERE a.id > b.id
  AND a.unique_identifier = b.unique_identifier;

-- Step 5: Add NOT NULL constraint to unique_identifier
ALTER TABLE subjects
ALTER COLUMN unique_identifier SET NOT NULL;

-- Step 6: Add unique constraint
ALTER TABLE subjects
ADD CONSTRAINT subjects_unique_identifier_key UNIQUE (unique_identifier);

-- Step 7: Create index
CREATE INDEX IF NOT EXISTS idx_subjects_unique_identifier
ON subjects(unique_identifier);

-- Step 8: Drop unique constraint from iin_bin (if exists)
ALTER TABLE subjects
DROP CONSTRAINT IF EXISTS subjects_iin_bin_key;

-- Keep index on iin_bin for searching
CREATE INDEX IF NOT EXISTS idx_subjects_iin_bin
ON subjects(iin_bin);

COMMIT;

-- Verification query
SELECT
    COUNT(*) as total_subjects,
    COUNT(unique_identifier) as with_identifier,
    COUNT(iin_bin) as with_iin_bin,
    COUNT(DISTINCT unique_identifier) as unique_identifiers
FROM subjects;
