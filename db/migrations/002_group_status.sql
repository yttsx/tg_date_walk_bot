ALTER TABLE group_members ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'accepted';

-- Index for fast pending-invite lookups
CREATE INDEX IF NOT EXISTS group_members_user_status_idx ON group_members(user_id, status);
