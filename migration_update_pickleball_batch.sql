-- Migration script to update event_registrations table
-- Change pickleball_level column to orangetheory_batch

-- Step 1: Add the new column
ALTER TABLE event_registrations ADD COLUMN orangetheory_batch VARCHAR;

-- Step 2: Copy data from old column to new column (if any existing data)
-- Note: This will be empty for new batch system, but keeping for safety
UPDATE event_registrations SET orangetheory_batch = pickleball_level WHERE pickleball_level IS NOT NULL;

-- Step 3: Drop the old column
ALTER TABLE event_registrations DROP COLUMN pickleball_level;

-- Step 4: Verify the change
-- You can run: SELECT column_name FROM information_schema.columns WHERE table_name = 'event_registrations';
