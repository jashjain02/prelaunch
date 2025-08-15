-- Migration script to update event_registrations table for Orangetheory event
-- This script should be run on the production database

-- Step 1: Add the new column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'event_registrations' 
                   AND column_name = 'orangetheory_batch') THEN
        ALTER TABLE event_registrations ADD COLUMN orangetheory_batch VARCHAR;
    END IF;
END $$;

-- Step 2: Copy data from old column to new column (if any existing data)
-- Note: This will be empty for new batch system, but keeping for safety
UPDATE event_registrations 
SET orangetheory_batch = pickleball_level 
WHERE pickleball_level IS NOT NULL 
AND orangetheory_batch IS NULL;

-- Step 3: Drop the old column if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'event_registrations' 
               AND column_name = 'pickleball_level') THEN
        ALTER TABLE event_registrations DROP COLUMN pickleball_level;
    END IF;
END $$;

-- Step 4: Verify the change
-- You can run: SELECT column_name FROM information_schema.columns WHERE table_name = 'event_registrations';

-- Step 5: Update any existing registrations to use the new event name
-- This updates any old "pickleball" references to "orangetheory" in selected_sports
UPDATE event_registrations 
SET selected_sports = REPLACE(selected_sports, 'pickleball', 'orangetheory')
WHERE selected_sports LIKE '%pickleball%';

-- Step 6: Create index on orangetheory_batch for better query performance
CREATE INDEX IF NOT EXISTS idx_event_registrations_orangetheory_batch 
ON event_registrations(orangetheory_batch);

-- Step 7: Add new columns for enhanced event tracking
ALTER TABLE event_registrations ADD COLUMN IF NOT EXISTS event_date VARCHAR DEFAULT '24th August 2025';
ALTER TABLE event_registrations ADD COLUMN IF NOT EXISTS event_location VARCHAR DEFAULT 'Orangetheory Fitness, Worli';
ALTER TABLE event_registrations ADD COLUMN IF NOT EXISTS payment_status VARCHAR DEFAULT 'pending';
ALTER TABLE event_registrations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE event_registrations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Step 8: Create trigger for updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_event_registrations_updated_at ON event_registrations;
CREATE TRIGGER update_event_registrations_updated_at
    BEFORE UPDATE ON event_registrations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Step 9: Add comments to document the changes
COMMENT ON COLUMN event_registrations.orangetheory_batch IS 'Batch selection for Orangetheory event (batch1: 7:30-8:30 AM, batch2: 9:00-10:00 AM)';
COMMENT ON COLUMN event_registrations.event_date IS 'Event date (e.g., 24th August 2025)';
COMMENT ON COLUMN event_registrations.event_location IS 'Event location (e.g., Orangetheory Fitness, Worli)';
COMMENT ON COLUMN event_registrations.payment_status IS 'Payment status: pending, completed, failed';
COMMENT ON COLUMN event_registrations.is_active IS 'Soft delete flag - TRUE for active registrations';
COMMENT ON COLUMN event_registrations.updated_at IS 'Last update timestamp';
