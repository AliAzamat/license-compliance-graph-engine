CREATE TABLE IF NOT EXISTS nodes (
    id          UUID PRIMARY KEY,
    type        TEXT        NOT NULL,
    key         TEXT        NOT NULL,
    label       TEXT        NOT NULL,
    attrs       JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (type, key)
);

CREATE TABLE IF NOT EXISTS edges (
    id          UUID PRIMARY KEY,
    src_id      UUID        NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    dst_id      UUID        NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
    type        TEXT        NOT NULL,
    attrs       JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (src_id, dst_id, type)
);

CREATE INDEX IF NOT EXISTS edges_src_type_idx ON edges (src_id, type);

-- Append-only audit: one row per compliance answer we returned. Never updated,
-- never deleted. This is the record that lets us defend any answer we gave.
CREATE TABLE IF NOT EXISTS audit_log (
    id            UUID PRIMARY KEY,
    entity_key    TEXT        NOT NULL,
    request       JSONB       NOT NULL,          -- the inputs (entity, last_filed)
    facts         JSONB       NOT NULL,          -- the graph facts used
    response      JSONB       NOT NULL,          -- the grounded checklist returned
    grounded_ratio NUMERIC    NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
