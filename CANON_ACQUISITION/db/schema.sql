-- CANON_ACQUISITION — Postgres schema (spec section 53, 57).
-- Mirrors the 37 JSONL datasets emitted by run_all.py. Graph is modelled with
-- adjacency tables (dependency / relationship); Neo4j NOT required for P0 (sec 53).
-- Vector index uses pgvector (sec 52).
--
-- Apply:  psql "$CANON_DB" -f db/schema.sql

CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector (section 52)

-- ---- enums (kept as CHECKed text for portability) ------------------------
-- trust_tier: 0..5 (section 2)   knowledge_state: KNOWN/SUPPORTED/INFERRED/AMBIGUOUS/UNKNOWN/CONFLICTED/STALE (55)

-- 01 sources (section 32/59) ------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    source_id           text PRIMARY KEY,
    source_url          text,
    canonical_url       text,
    publisher           text NOT NULL,
    manufacturer        text,
    title               text NOT NULL,
    document_type       text,
    product_family      text,
    product_model       text,
    version             text,
    revision            text,
    publication_date    text,
    last_updated        text,
    language            text DEFAULT 'en',
    region              text,
    access_type         text DEFAULT 'PUBLIC',
    license             text,
    trust_tier          smallint NOT NULL CHECK (trust_tier BETWEEN 0 AND 5),
    retrieval_timestamp timestamptz,
    content_hash        text,
    mime_type           text,
    file_size           bigint,
    parser              text,
    parser_version      text,
    status              text DEFAULT 'DISCOVERED'
);

-- 02 documents / 03 revisions ----------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    document_id    text PRIMARY KEY,
    source_id      text REFERENCES sources(source_id),
    title          text,
    document_type  text,
    content_hash   text,
    mime_type      text,
    page_count     int,
    file_path      text,
    classification text,
    status         text DEFAULT 'PROCESSED'
);
CREATE TABLE IF NOT EXISTS document_revisions (
    revision_id  text PRIMARY KEY,
    document_id  text REFERENCES documents(document_id),
    content_hash text NOT NULL,
    supersedes   text,
    note         text,
    created_at   timestamptz
);

-- 04 entities / 05 aliases (section 37/38) ---------------------------------
CREATE TABLE IF NOT EXISTS entities (
    entity_id       text PRIMARY KEY,
    kind            text NOT NULL,          -- ENTITY_KINDS
    name            text NOT NULL,
    machine_id      text,
    parent          text,
    knowledge_state text DEFAULT 'KNOWN',
    truth_status    text DEFAULT 'PROPOSED',
    attributes      jsonb DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS entities_kind_idx ON entities(kind);
CREATE INDEX IF NOT EXISTS entities_machine_idx ON entities(machine_id);

CREATE TABLE IF NOT EXISTS entity_aliases (
    entity_id         text REFERENCES entities(entity_id),
    alias             text NOT NULL,
    resolution_status text DEFAULT 'RESOLVED',
    confidence        text,
    evidence_id       text,
    PRIMARY KEY (entity_id, alias)
);

-- 06 signals / 07 io / 08 assets + typed asset tables ----------------------
CREATE TABLE IF NOT EXISTS signals (
    "signalId" text, asset text, kind text, "dataType" text,
    "engUnit" text, "engMin" double precision, "engMax" double precision,
    hh double precision, h double precision, l double precision, ll double precision,
    description text, access text, "truthStatus" text, machine text,
    PRIMARY KEY ("signalId", machine)
);
CREATE TABLE IF NOT EXISTS io (
    "signalId" text, area text, address int, dtype text, endian text,
    scale double precision, note text, source text, machine text
);
CREATE TABLE IF NOT EXISTS assets (
    asset_id text, type text, name text, machine text,
    "capacityLiters" double precision, geometry jsonb, truth_status text
);
CREATE TABLE IF NOT EXISTS controllers (
    "controllerId" text PRIMARY KEY, family text, protocols jsonb,
    "opcuaNamespace" text, "opcuaPort" int, "modbusPort" int,
    "scanTimeMs" int, machine text, "truthStatus" text, source text
);
CREATE TABLE IF NOT EXISTS modules      (module_id text, controller text, rack int, slot int, type text, machine text);
CREATE TABLE IF NOT EXISTS instruments  (tag text, asset text, unit text, range jsonb, hh double precision, h double precision, l double precision, ll double precision, description text, source text, machine text);
CREATE TABLE IF NOT EXISTS motors       (asset_id text, name text, "driveType" text, "ratedFlowM3h" double precision, machine text, truth_status text);
CREATE TABLE IF NOT EXISTS drives       (asset_id text, name text, model text, machine text, truth_status text);
CREATE TABLE IF NOT EXISTS valves       (asset_id text, name text, "valveType" text, machine text, truth_status text);

-- 15 commands / 16 permissives / 17 interlocks (section 12/13) -------------
CREATE TABLE IF NOT EXISTS commands (
    command_id text, target_asset text, request_signal text, feedback_signal text,
    authority text, "timeoutSec" int, source text, truth_status text, machine text
);
CREATE TABLE IF NOT EXISTS permissives (
    permissive_id text, command text, signal text, expected text,
    "rejectCode" text, message text, source text, machine text
);
CREATE TABLE IF NOT EXISTS interlocks (
    interlock_id text, command text, signal text, expected text, "appliesTo" text,
    type text, "onFail" text, "rejectCode" text, message text, source text, machine text
);

-- 18 alarms / 19 states / 20 modes / 21 sequences --------------------------
CREATE TABLE IF NOT EXISTS alarms (
    alarm_id text, signal text, condition text, priority text, class text,
    message text, source text, machine text, truth_status text
);
CREATE TABLE IF NOT EXISTS states (
    state_id text, device text, state text, "packmlMapping" text, source text, machine text
);
CREATE TABLE IF NOT EXISTS modes (
    mode_id text, mode text, knowledge_state text, note text, machine text
);
CREATE TABLE IF NOT EXISTS sequences (
    sequence_id text, kind text, device text, steps jsonb, "from" text, event text,
    "to" text, emit text, "timeoutSec" int, knowledge_state text, source text, machine text
);

-- 22 process relationships / 23-24 hmi -------------------------------------
CREATE TABLE IF NOT EXISTS process_relationships (subject text, predicate text, object text, source text, machine text);
CREATE TABLE IF NOT EXISTS hmi_screens (
    screen_id text, purpose text, asset_scope jsonb, operator_role text,
    visible_assets jsonb, commands jsonb, knowledge_state text, note text, source text
);
CREATE TABLE IF NOT EXISTS hmi_components (
    component text, category text, version text, states jsonb, commands jsonb,
    "extractableFromSchneider" boolean, source text
);

-- 25 protocols / 26 products / 27 standards / 28 procedures ----------------
CREATE TABLE IF NOT EXISTS protocols (id text, name text, standard text, status text, source text, detail jsonb);
CREATE TABLE IF NOT EXISTS products (
    manufacturer text, family text, model text, document_type text,
    documentation text, revision text, official_source text,
    capability_status text DEFAULT 'UNKNOWN', note text        -- section 22: never invent capability
);
CREATE TABLE IF NOT EXISTS standards (
    standard_id text PRIMARY KEY, title text, version text, publisher text,
    source_url text, access_status text, trust_tier smallint
);
CREATE TABLE IF NOT EXISTS procedures (procedure_id text, title text, steps jsonb, source text, machine text);

-- 29 facts / 31 evidence (section 33/34) — the evidence spine --------------
CREATE TABLE IF NOT EXISTS facts (
    fact_id         text PRIMARY KEY,
    subject         text NOT NULL,
    predicate       text NOT NULL,
    object          text,
    value           jsonb,
    unit            text,
    source_id       text NOT NULL REFERENCES sources(source_id),
    source_location text,
    page            text, section text, "table" text, paragraph text,
    evidence_text   text,
    evidence_id     text,
    confidence      text,
    trust_tier      smallint,
    knowledge_state text DEFAULT 'KNOWN',
    extraction_method text,
    created_at      timestamptz,
    revision        text,
    valid_from      timestamptz, valid_to timestamptz
);
CREATE INDEX IF NOT EXISTS facts_subject_idx ON facts(subject);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id     text PRIMARY KEY,
    fact_id         text NOT NULL REFERENCES facts(fact_id),
    source_id       text NOT NULL REFERENCES sources(source_id),
    source_location text NOT NULL,
    evidence_text   text NOT NULL,
    trust_tier      smallint,
    extraction_method text
);

-- 30 relationships / 34 dependencies (adjacency graph, section 39/53) ------
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id text PRIMARY KEY,
    subject         text NOT NULL,
    predicate       text NOT NULL,          -- RELATIONSHIP_PREDICATES
    object          text NOT NULL,
    source_id       text,
    evidence_id     text,
    confidence      text,
    knowledge_state text DEFAULT 'KNOWN'
);
CREATE INDEX IF NOT EXISTS rel_subject_idx ON relationships(subject);
CREATE INDEX IF NOT EXISTS rel_object_idx  ON relationships(object);

CREATE TABLE IF NOT EXISTS dependencies (
    dependency_id text PRIMARY KEY,
    from_entity   text NOT NULL,
    edge_type     text NOT NULL,            -- BINDS/READS/WRITES/PERMITS/TRIGGERS/DOCUMENTS/TESTS/ALARMS/SCALES
    to_entity     text NOT NULL,
    revision_id   text
);
-- change-impact walk (section 36):
--   WITH RECURSIVE impact AS (
--     SELECT to_entity, edge_type, 1 AS depth FROM dependencies
--       WHERE from_entity = :changed AND revision_id = :rev
--     UNION ALL
--     SELECT d.to_entity, d.edge_type, i.depth+1 FROM dependencies d
--       JOIN impact i ON d.from_entity = i.to_entity WHERE i.depth < 10)
--   SELECT * FROM impact;

-- 32 conflicts / 33 unknowns / 35 change history (section 35/50/61) --------
CREATE TABLE IF NOT EXISTS conflicts (
    conflict_id     text PRIMARY KEY,
    subject         text, property text,
    value_a jsonb, source_a text, value_b jsonb, source_b text,
    source_trust_a smallint, source_trust_b smallint,
    revision_a text, revision_b text,
    resolution_status text DEFAULT 'UNRESOLVED',
    resolution_note text
);
CREATE TABLE IF NOT EXISTS unknowns (
    unknown_id text PRIMARY KEY, kind text, subject text, reason text,
    review_required boolean DEFAULT true,
    filename text, mime text, hash text, size bigint,
    detected_structure text, possible_type text
);
CREATE TABLE IF NOT EXISTS change_history (
    change_id text PRIMARY KEY, change_type text, entity text, field text,
    from_value jsonb, to_value jsonb, from_revision text, to_revision text,
    action text, review_required boolean DEFAULT false
);

-- 36 context packs / 37 embeddings (section 40/52) -------------------------
CREATE TABLE IF NOT EXISTS context_packs (
    machine_id text, generated timestamptz, pack jsonb
);
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id text PRIMARY KEY,
    ref_kind text, ref_id text, text text,
    vector vector(16),                       -- P0 placeholder dim; widen for a real model
    dim int, method text, note text,
    vendor text, product text, trust_tier smallint, machine text
);
-- CREATE INDEX embeddings_vec_idx ON embeddings USING ivfflat (vector vector_cosine_ops);
