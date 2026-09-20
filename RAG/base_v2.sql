-- HVNH Hub unified data model v2
-- PostgreSQL 16+. PostgreSQL is the source of truth; R2 stores binary objects;
-- Qdrant stores embeddings keyed by ai_document_chunks.id.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE account_status AS ENUM ('PENDING', 'ACTIVE', 'LOCKED', 'DISABLED');
CREATE TYPE group_role AS ENUM ('MEMBER', 'ADMIN');
CREATE TYPE group_status AS ENUM ('ACTIVE', 'ARCHIVED');
CREATE TYPE post_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'HIDDEN');
CREATE TYPE friend_request_status AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED');
CREATE TYPE conversation_type AS ENUM ('DIRECT', 'GROUP');
CREATE TYPE message_type AS ENUM ('TEXT', 'IMAGE', 'FILE', 'SYSTEM');
CREATE TYPE notification_type AS ENUM ('POST_REVIEW', 'POST_LIKE', 'COMMENT', 'FRIEND_REQUEST', 'MESSAGE', 'SYSTEM');
CREATE TYPE report_status AS ENUM ('PENDING', 'REVIEWING', 'RESOLVED', 'REJECTED');
CREATE TYPE report_target_type AS ENUM ('USER', 'POST', 'COMMENT');
CREATE TYPE ai_document_type AS ENUM ('REGULATION', 'ANNOUNCEMENT', 'FAQ', 'GUIDE', 'DECISION', 'OTHER');
CREATE TYPE ai_document_status AS ENUM ('PENDING', 'PROCESSING', 'INDEXED', 'FAILED', 'ARCHIVED');
CREATE TYPE ai_visibility AS ENUM ('PUBLIC', 'AUTHENTICATED', 'GROUP', 'PRIVATE');
CREATE TYPE ai_message_role AS ENUM ('SYSTEM', 'USER', 'ASSISTANT');

-- Identity and authorization
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(255) NOT NULL,
    username varchar(100) NOT NULL,
    password_hash text NOT NULL,
    status account_status NOT NULL DEFAULT 'PENDING',
    email_verified_at timestamptz,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT ck_users_hvnh_email CHECK (lower(email) ~ '^[^@]+@hvnh\.edu\.vn$')
);

CREATE TABLE profiles (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    student_code varchar(50) UNIQUE,
    full_name varchar(150) NOT NULL,
    avatar_object_key text,
    bio text,
    faculty varchar(150),
    cohort varchar(50),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_profiles_full_name_trgm ON profiles USING gin (full_name gin_trgm_ops);

CREATE TABLE roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    description text
);

CREATE TABLE user_roles (
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE email_verification_codes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash text NOT NULL,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_email_code_expiry CHECK (expires_at > created_at)
);
CREATE INDEX idx_email_codes_user_active ON email_verification_codes(user_id, expires_at DESC)
    WHERE consumed_at IS NULL;

CREATE TABLE refresh_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    replaced_by_id uuid REFERENCES refresh_tokens(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id, expires_at DESC);

-- Groups, content and moderation
CREATE TABLE groups (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(150) NOT NULL,
    slug varchar(160) NOT NULL UNIQUE,
    description text,
    cover_object_key text,
    status group_status NOT NULL DEFAULT 'ACTIVE',
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE group_members (
    group_id uuid NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role group_role NOT NULL DEFAULT 'MEMBER',
    joined_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (group_id, user_id)
);
CREATE INDEX idx_group_members_user ON group_members(user_id, joined_at DESC);

CREATE TABLE posts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id uuid NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    author_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    content text NOT NULL,
    status post_status NOT NULL DEFAULT 'PENDING',
    reviewed_by uuid REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at timestamptz,
    rejection_reason text,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(content, ''))) STORED,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);
CREATE INDEX idx_posts_feed ON posts(group_id, status, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_posts_author ON posts(author_id, created_at DESC);
CREATE INDEX idx_posts_search ON posts USING gin(search_vector);

CREATE TABLE media_files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid REFERENCES users(id) ON DELETE SET NULL,
    bucket varchar(100) NOT NULL,
    object_key text NOT NULL,
    original_name varchar(500),
    mime_type varchar(150) NOT NULL,
    file_size bigint NOT NULL,
    checksum_sha256 varchar(64),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_media_object UNIQUE(bucket, object_key),
    CONSTRAINT ck_media_file_size CHECK(file_size >= 0)
);

CREATE TABLE post_media (
    post_id uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    media_id uuid NOT NULL REFERENCES media_files(id) ON DELETE RESTRICT,
    sort_order integer NOT NULL DEFAULT 0,
    PRIMARY KEY(post_id, media_id),
    CONSTRAINT uq_post_media_order UNIQUE(post_id, sort_order)
);

CREATE TABLE comments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    parent_id uuid REFERENCES comments(id) ON DELETE CASCADE,
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);
CREATE INDEX idx_comments_post ON comments(post_id, created_at);

CREATE TABLE post_likes (
    post_id uuid NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(post_id, user_id)
);

CREATE TABLE reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id uuid REFERENCES users(id) ON DELETE SET NULL,
    target_type report_target_type NOT NULL,
    target_id uuid NOT NULL,
    reason text NOT NULL,
    status report_status NOT NULL DEFAULT 'PENDING',
    handled_by uuid REFERENCES users(id) ON DELETE SET NULL,
    resolution_note text,
    handled_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_reports_queue ON reports(status, created_at);

-- Social graph
CREATE TABLE friend_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status friend_request_status NOT NULL DEFAULT 'PENDING',
    responded_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_friend_request_distinct CHECK(sender_id <> receiver_id)
);
CREATE UNIQUE INDEX uq_pending_friend_pair ON friend_requests(
    LEAST(sender_id, receiver_id), GREATEST(sender_id, receiver_id)
) WHERE status = 'PENDING';

CREATE TABLE friendships (
    user_low_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_high_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(user_low_id, user_high_id),
    CONSTRAINT ck_friendship_order CHECK(user_low_id < user_high_id)
);
CREATE INDEX idx_friendships_high ON friendships(user_high_id);

CREATE TABLE user_blocks (
    blocker_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(blocker_id, blocked_id),
    CONSTRAINT ck_user_block_distinct CHECK(blocker_id <> blocked_id)
);

-- Realtime chat. Delivery/read state belongs to each recipient, not the message globally.
CREATE TABLE conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    type conversation_type NOT NULL DEFAULT 'DIRECT',
    title varchar(255),
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    last_message_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE conversation_members (
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at timestamptz NOT NULL DEFAULT now(),
    left_at timestamptz,
    PRIMARY KEY(conversation_id, user_id)
);
CREATE INDEX idx_conversation_members_user ON conversation_members(user_id, conversation_id);

CREATE TABLE messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id uuid REFERENCES users(id) ON DELETE SET NULL,
    message_type message_type NOT NULL DEFAULT 'TEXT',
    content text,
    reply_to_id uuid REFERENCES messages(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    edited_at timestamptz,
    deleted_at timestamptz,
    CONSTRAINT ck_message_has_content CHECK(content IS NOT NULL OR message_type IN ('IMAGE', 'FILE'))
);
CREATE INDEX idx_messages_realtime ON messages(conversation_id, created_at DESC);

CREATE TABLE message_attachments (
    message_id uuid NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    media_id uuid NOT NULL REFERENCES media_files(id) ON DELETE RESTRICT,
    PRIMARY KEY(message_id, media_id)
);

CREATE TABLE message_receipts (
    message_id uuid NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delivered_at timestamptz,
    seen_at timestamptz,
    PRIMARY KEY(message_id, user_id),
    CONSTRAINT ck_receipt_order CHECK(seen_at IS NULL OR delivered_at IS NULL OR seen_at >= delivered_at)
);

CREATE TABLE notifications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title varchar(255) NOT NULL,
    content text,
    actor_id uuid REFERENCES users(id) ON DELETE SET NULL,
    reference_type varchar(50),
    reference_id uuid,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    read_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_unread ON notifications(user_id, created_at DESC) WHERE read_at IS NULL;

-- AI/RAG knowledge. Logical document -> immutable versions -> immutable chunks.
CREATE TABLE ai_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_code varchar(100),
    title varchar(500) NOT NULL,
    document_type ai_document_type NOT NULL DEFAULT 'OTHER',
    academic_year varchar(9),
    issuer varchar(255),
    published_at timestamptz,
    effective_from timestamptz,
    effective_to timestamptz,
    visibility ai_visibility NOT NULL DEFAULT 'PUBLIC',
    group_id uuid REFERENCES groups(id) ON DELETE SET NULL,
    owner_id uuid REFERENCES users(id) ON DELETE SET NULL,
    current_version_id uuid,
    is_current boolean NOT NULL DEFAULT true,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT ck_ai_academic_year CHECK(academic_year IS NULL OR academic_year ~ '^[0-9]{4}/[0-9]{4}$'),
    CONSTRAINT ck_ai_effective_period CHECK(effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from)
);
CREATE INDEX idx_ai_documents_retrieval ON ai_documents(document_type, academic_year, is_current, published_at DESC);
CREATE INDEX idx_ai_documents_metadata ON ai_documents USING gin(metadata);

CREATE TABLE ai_document_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES ai_documents(id) ON DELETE RESTRICT,
    version_number integer NOT NULL,
    version_label varchar(100),
    source_type varchar(50) NOT NULL,
    source_url text,
    file_object_key text,
    mime_type varchar(100),
    content_hash varchar(64) NOT NULL,
    raw_content text,
    status ai_document_status NOT NULL DEFAULT 'PENDING',
    error_message text,
    embedding_model varchar(255),
    chunking_version varchar(50),
    indexed_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ai_document_version UNIQUE(document_id, version_number),
    CONSTRAINT uq_ai_document_hash UNIQUE(document_id, content_hash),
    CONSTRAINT ck_ai_version_positive CHECK(version_number > 0),
    CONSTRAINT ck_ai_source CHECK(source_url IS NOT NULL OR file_object_key IS NOT NULL)
);
ALTER TABLE ai_documents ADD CONSTRAINT fk_ai_current_version
    FOREIGN KEY(current_version_id) REFERENCES ai_document_versions(id) ON DELETE SET NULL;
CREATE INDEX idx_ai_versions_status ON ai_document_versions(status, created_at);

CREATE TABLE ai_document_chunks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id uuid NOT NULL REFERENCES ai_document_versions(id) ON DELETE RESTRICT,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    content_hash varchar(64) NOT NULL,
    token_count integer NOT NULL,
    page_start integer,
    page_end integer,
    section_title varchar(500),
    heading_path jsonb NOT NULL DEFAULT '[]'::jsonb,
    start_offset integer,
    end_offset integer,
    qdrant_point_id uuid NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ai_chunk_index UNIQUE(document_version_id, chunk_index),
    CONSTRAINT uq_ai_qdrant_point UNIQUE(qdrant_point_id),
    CONSTRAINT ck_ai_chunk_index CHECK(chunk_index >= 0),
    CONSTRAINT ck_ai_chunk_tokens CHECK(token_count > 0),
    CONSTRAINT ck_ai_chunk_pages CHECK(page_end IS NULL OR page_start IS NULL OR page_end >= page_start)
);
CREATE INDEX idx_ai_chunks_version ON ai_document_chunks(document_version_id, chunk_index);

CREATE TABLE ai_document_relations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_version_id uuid NOT NULL REFERENCES ai_document_versions(id) ON DELETE CASCADE,
    target_document_id uuid REFERENCES ai_documents(id) ON DELETE SET NULL,
    referenced_number varchar(100) NOT NULL,
    relation_type varchar(30) NOT NULL DEFAULT 'REFERENCES',
    context_excerpt text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ai_document_relation UNIQUE(source_document_version_id, referenced_number, relation_type),
    CONSTRAINT ck_ai_document_relation_type CHECK(
        relation_type IN ('REFERENCES','AMENDS','SUPERSEDES','REPEALS')
    )
);
CREATE INDEX idx_ai_document_relations_source ON ai_document_relations(source_document_version_id);
CREATE INDEX idx_ai_document_relations_target ON ai_document_relations(target_document_id);
CREATE INDEX idx_ai_document_relations_number ON ai_document_relations(referenced_number);

-- AI conversations are separate from student-to-student chat.
CREATE TABLE ai_conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    title varchar(500),
    summary text,
    summary_until_sequence integer NOT NULL DEFAULT 0,
    academic_year_context varchar(9),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    last_message_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT ck_ai_conversation_year CHECK(academic_year_context IS NULL OR academic_year_context ~ '^[0-9]{4}/[0-9]{4}$')
);
CREATE INDEX idx_ai_conversations_user ON ai_conversations(user_id, updated_at DESC);

CREATE TABLE ai_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    sequence_number integer NOT NULL,
    role ai_message_role NOT NULL,
    content text NOT NULL,
    rewritten_question text,
    retrieval_filters jsonb NOT NULL DEFAULT '{}'::jsonb,
    model_name varchar(255),
    prompt_tokens integer,
    completion_tokens integer,
    latency_ms integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ai_message_sequence UNIQUE(conversation_id, sequence_number),
    CONSTRAINT ck_ai_message_sequence CHECK(sequence_number > 0)
);
CREATE INDEX idx_ai_messages_history ON ai_messages(conversation_id, sequence_number);

CREATE TABLE ai_message_citations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id uuid NOT NULL REFERENCES ai_messages(id) ON DELETE CASCADE,
    chunk_id uuid NOT NULL REFERENCES ai_document_chunks(id) ON DELETE RESTRICT,
    citation_order integer NOT NULL,
    retrieval_rank integer,
    relevance_score double precision,
    quoted_text text,
    document_title_snapshot varchar(500) NOT NULL,
    source_url_snapshot text,
    source_label_snapshot varchar(255),
    page_start_snapshot integer,
    page_end_snapshot integer,
    section_title_snapshot varchar(500),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ai_citation_order UNIQUE(message_id, citation_order),
    CONSTRAINT uq_ai_citation_chunk UNIQUE(message_id, chunk_id),
    CONSTRAINT ck_ai_citation_order CHECK(citation_order > 0)
);
CREATE INDEX idx_ai_citations_message ON ai_message_citations(message_id, citation_order);

CREATE TABLE audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id uuid REFERENCES users(id) ON DELETE SET NULL,
    action varchar(100) NOT NULL,
    target_type varchar(50) NOT NULL,
    target_id uuid,
    ip_address inet,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_type, target_id, created_at DESC);
