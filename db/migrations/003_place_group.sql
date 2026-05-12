ALTER TABLE places ADD COLUMN IF NOT EXISTS group_id INTEGER REFERENCES groups(id);

CREATE INDEX IF NOT EXISTS places_group_id_idx ON places(group_id);
