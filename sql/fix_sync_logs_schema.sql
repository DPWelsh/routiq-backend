-- Fix sync_logs table schema - Add missing updated_at column
-- This fixes the error: column "updated_at" of relation "sync_logs" does not exist

-- Add missing updated_at column
ALTER TABLE sync_logs 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create trigger to automatically update updated_at on changes
CREATE OR REPLACE FUNCTION update_sync_logs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to sync_logs table
DROP TRIGGER IF EXISTS update_sync_logs_updated_at_trigger ON sync_logs;
CREATE TRIGGER update_sync_logs_updated_at_trigger
    BEFORE UPDATE ON sync_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_logs_updated_at();

-- Verify the fix
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'sync_logs' 
AND column_name = 'updated_at'; 