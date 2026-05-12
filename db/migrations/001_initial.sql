CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username    VARCHAR(64),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS places (
    id           SERIAL PRIMARY KEY,
    owner_id     INTEGER NOT NULL REFERENCES users(id),
    title        VARCHAR(200) NOT NULL,
    address      VARCHAR(400) NOT NULL,
    lat          DOUBLE PRECISION,
    lon          DOUBLE PRECISION,
    geom         GEOMETRY(Point, 4326),
    url          VARCHAR(500),
    tags         JSONB DEFAULT '[]',
    city         VARCHAR(64) DEFAULT 'moscow',
    visibility   VARCHAR(16) DEFAULT 'private',
    working_hours JSONB,
    rating_avg   FLOAT DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    status       VARCHAR(16) DEFAULT 'active',
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS places_geom_idx ON places USING GIST(geom);
CREATE INDEX IF NOT EXISTS places_owner_idx ON places(owner_id);
CREATE INDEX IF NOT EXISTS places_tags_idx ON places USING GIN(tags);

CREATE TABLE IF NOT EXISTS groups (
    id         SERIAL PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_members (
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id  INTEGER NOT NULL REFERENCES users(id),
    role     VARCHAR(16) DEFAULT 'member',
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE IF NOT EXISTS scenario_templates (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(64) UNIQUE NOT NULL,
    participant_min SMALLINT DEFAULT 1,
    participant_max SMALLINT DEFAULT 99,
    steps_json      JSONB NOT NULL,
    active          BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS generated_routes (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    group_id     INTEGER REFERENCES groups(id),
    scenario_id  INTEGER REFERENCES scenario_templates(id),
    places_json  JSONB NOT NULL,
    distance_m   INTEGER,
    walk_minutes INTEGER,
    total_minutes INTEGER,
    rating_avg   FLOAT DEFAULT 0,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ratings (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    place_id   INTEGER REFERENCES places(id),
    route_id   INTEGER REFERENCES generated_routes(id),
    value      SMALLINT NOT NULL CHECK (value BETWEEN 1 AND 5),
    text       TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed scenario templates
-- Tags are simplified to 3 categories: cafe | park | food
INSERT INTO scenario_templates (name, participant_min, participant_max, steps_json) VALUES
(
    'date',
    2, 2,
    '[
        {"step": 1, "label": "☕ Кофе", "tags": ["cafe"], "duration_min": 30},
        {"step": 2, "label": "🏞️ Прогулка", "tags": ["park"], "duration_min": 40},
        {"step": 3, "label": "🍴 Ужин", "tags": ["food"], "duration_min": 60}
    ]'
),
(
    'walk',
    3, 99,
    '[
        {"step": 1, "label": "☕ Кофе", "tags": ["cafe"], "duration_min": 20},
        {"step": 2, "label": "🏞️ Парк", "tags": ["park"], "duration_min": 60},
        {"step": 3, "label": "🍴 Еда", "tags": ["food"], "duration_min": 45}
    ]'
),
(
    'light',
    1, 99,
    '[
        {"step": 1, "label": "☕ Кофе", "tags": ["cafe"], "duration_min": 30},
        {"step": 2, "label": "🏞️ Парк", "tags": ["park"], "duration_min": 45}
    ]'
)
ON CONFLICT (name) DO UPDATE SET steps_json = EXCLUDED.steps_json;
