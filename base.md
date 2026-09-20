CREATE SCHEMA IF NOT EXISTS "public";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE TYPE "account_status" AS ENUM('PENDING', 'ACTIVE', 'LOCKED', 'DISABLED');
CREATE TYPE "group_role" AS ENUM('MEMBER', 'ADMIN');
CREATE TYPE "system_role" AS ENUM('USER', 'SUPER_ADMIN');
CREATE TYPE "group_join_request_status" AS ENUM('PENDING', 'APPROVED', 'REJECTED');
CREATE TYPE "group_status" AS ENUM('ACTIVE', 'ARCHIVED');
CREATE TYPE "post_status" AS ENUM('PENDING', 'APPROVED', 'REJECTED', 'HIDDEN');
CREATE TYPE "post_visibility" AS ENUM('PUBLIC', 'FRIENDS', 'PRIVATE');
CREATE TYPE "post_type" AS ENUM('STANDARD', 'PROFILE_POST', 'PROFILE_AVATAR', 'PROFILE_COVER');
CREATE TYPE "media_status" AS ENUM('PENDING', 'READY', 'FAILED', 'DELETED');
CREATE TYPE "friend_request_status" AS ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED');
CREATE TYPE "conversation_type" AS ENUM('DIRECT', 'GROUP');
CREATE TYPE "message_type" AS ENUM('TEXT', 'IMAGE', 'FILE', 'SYSTEM');
CREATE TYPE "notification_type" AS ENUM('POST_REVIEW', 'POST_LIKE', 'COMMENT', 'FRIEND_REQUEST', 'MESSAGE', 'SYSTEM');
CREATE TYPE "report_status" AS ENUM('PENDING', 'REVIEWING', 'RESOLVED', 'REJECTED');
CREATE TYPE "report_target_type" AS ENUM('USER', 'POST', 'COMMENT');
CREATE TYPE "ai_document_type" AS ENUM('REGULATION', 'ANNOUNCEMENT', 'FAQ', 'GUIDE', 'DECISION', 'OTHER');
CREATE TYPE "ai_document_status" AS ENUM('PENDING', 'PROCESSING', 'INDEXED', 'FAILED', 'ARCHIVED');
CREATE TYPE "ai_visibility" AS ENUM('PUBLIC', 'AUTHENTICATED', 'GROUP', 'PRIVATE');
CREATE TYPE "ai_message_role" AS ENUM('SYSTEM', 'USER', 'ASSISTANT');
CREATE TABLE "ai_conversations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"title" varchar(500),
	"summary" text,
	"summary_until_sequence" integer DEFAULT 0 NOT NULL,
	"academic_year_context" varchar(9),
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"last_message_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deleted_at" timestamp with time zone,
	CONSTRAINT "ck_ai_conversation_year" CHECK (((academic_year_context IS NULL) OR ((academic_year_context)::text ~ '^[0-9]{4}/[0-9]{4}$'::text)))
);
CREATE TABLE "ai_crawl_items" (
	"run_id" uuid NOT NULL,
	"source_url_id" uuid,
	"url" text NOT NULL,
	"url_hash" varchar(64) NOT NULL,
	"status" varchar(20) DEFAULT 'DISCOVERED' NOT NULL,
	"depth" integer NOT NULL,
	"discovered_from" text,
	"http_status" integer,
	"content_type" varchar(255),
	"response_bytes" integer,
	"document_version_id" uuid,
	"error_code" varchar(100),
	"started_at" timestamp with time zone,
	"finished_at" timestamp with time zone,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"id" uuid DEFAULT gen_random_uuid(),
	CONSTRAINT "pk_ai_crawl_items" PRIMARY KEY("id"),
	CONSTRAINT "uq_ai_crawl_item_url" UNIQUE("run_id","url_hash"),
	CONSTRAINT "ck_ai_crawl_items_ck_ai_crawl_items_ai_crawl_item_depth" CHECK ((depth >= 0)),
	CONSTRAINT "ck_ai_crawl_items_ck_ai_crawl_items_ai_crawl_item_status" CHECK (((status)::text = ANY ((ARRAY['DISCOVERED'::character varying, 'FETCHING'::character varying, 'UNCHANGED'::character varying, 'DOWNLOADED'::character varying, 'EXTRACTED'::character varying, 'SAVED'::character varying, 'REJECTED'::character varying, 'FAILED'::character varying])::text[])))
);
CREATE TABLE "ai_crawl_runs" (
	"source_id" uuid NOT NULL,
	"status" varchar(20) DEFAULT 'PENDING' NOT NULL,
	"trigger_type" varchar(20) DEFAULT 'SCHEDULED' NOT NULL,
	"queued_at" timestamp with time zone DEFAULT now() NOT NULL,
	"started_at" timestamp with time zone,
	"finished_at" timestamp with time zone,
	"pages_discovered" integer DEFAULT 0 NOT NULL,
	"pages_fetched" integer DEFAULT 0 NOT NULL,
	"documents_created" integer DEFAULT 0 NOT NULL,
	"documents_unchanged" integer DEFAULT 0 NOT NULL,
	"items_failed" integer DEFAULT 0 NOT NULL,
	"error_code" varchar(100),
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"id" uuid DEFAULT gen_random_uuid(),
	CONSTRAINT "pk_ai_crawl_runs" PRIMARY KEY("id"),
	CONSTRAINT "ck_ai_crawl_runs_ck_ai_crawl_runs_ai_crawl_run_status" CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'QUEUED'::character varying, 'RUNNING'::character varying, 'SUCCEEDED'::character varying, 'PARTIAL'::character varying, 'FAILED'::character varying, 'CANCELLED'::character varying])::text[]))),
	CONSTRAINT "ck_ai_crawl_runs_ck_ai_crawl_runs_ai_crawl_trigger" CHECK (((trigger_type)::text = ANY ((ARRAY['SCHEDULED'::character varying, 'MANUAL'::character varying, 'RECOVERY'::character varying])::text[])))
);
CREATE TABLE "ai_document_chunks" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"document_version_id" uuid NOT NULL,
	"chunk_index" integer NOT NULL,
	"content" text NOT NULL,
	"content_hash" varchar(64) NOT NULL,
	"token_count" integer NOT NULL,
	"page_start" integer,
	"page_end" integer,
	"section_title" varchar(500),
	"heading_path" jsonb DEFAULT '[]' NOT NULL,
	"start_offset" integer,
	"end_offset" integer,
	"qdrant_point_id" uuid NOT NULL CONSTRAINT "uq_ai_qdrant_point" UNIQUE,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "uq_ai_chunk_index" UNIQUE("document_version_id","chunk_index"),
	CONSTRAINT "ck_ai_chunk_index" CHECK ((chunk_index >= 0)),
	CONSTRAINT "ck_ai_chunk_pages" CHECK (((page_end IS NULL) OR (page_start IS NULL) OR (page_end >= page_start))),
	CONSTRAINT "ck_ai_chunk_tokens" CHECK ((token_count > 0))
);
CREATE TABLE "ai_document_relations" (
	"source_document_version_id" uuid NOT NULL,
	"target_document_id" uuid,
	"referenced_number" varchar(100) NOT NULL,
	"relation_type" varchar(30) DEFAULT 'REFERENCES' NOT NULL,
	"context_excerpt" text,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"id" uuid DEFAULT gen_random_uuid(),
	CONSTRAINT "pk_ai_document_relations" PRIMARY KEY("id"),
	CONSTRAINT "uq_ai_document_relation" UNIQUE("source_document_version_id","referenced_number","relation_type"),
	CONSTRAINT "ck_ai_document_relations_ck_ai_document_relations_ai_do_d993" CHECK (((relation_type)::text = ANY ((ARRAY['REFERENCES'::character varying, 'AMENDS'::character varying, 'SUPERSEDES'::character varying, 'REPEALS'::character varying])::text[])))
);
CREATE TABLE "ai_document_versions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"document_id" uuid NOT NULL,
	"version_number" integer NOT NULL,
	"version_label" varchar(100),
	"source_type" varchar(50) NOT NULL,
	"source_url" text,
	"file_object_key" text,
	"mime_type" varchar(100),
	"content_hash" varchar(64) NOT NULL,
	"raw_content" text,
	"status" ai_document_status DEFAULT 'PENDING' NOT NULL,
	"error_message" text,
	"embedding_model" varchar(255),
	"chunking_version" varchar(50),
	"indexed_at" timestamp with time zone,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "uq_ai_document_hash" UNIQUE("document_id","content_hash"),
	CONSTRAINT "uq_ai_document_version" UNIQUE("document_id","version_number"),
	CONSTRAINT "ck_ai_source" CHECK (((source_url IS NOT NULL) OR (file_object_key IS NOT NULL))),
	CONSTRAINT "ck_ai_version_positive" CHECK ((version_number > 0))
);
CREATE TABLE "ai_documents" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"document_code" varchar(100),
	"title" varchar(500) NOT NULL,
	"document_type" ai_document_type DEFAULT 'OTHER' NOT NULL,
	"academic_year" varchar(9),
	"issuer" varchar(255),
	"published_at" timestamp with time zone,
	"effective_from" timestamp with time zone,
	"effective_to" timestamp with time zone,
	"visibility" ai_visibility DEFAULT 'PUBLIC' NOT NULL,
	"group_id" uuid,
	"owner_id" uuid,
	"current_version_id" uuid,
	"is_current" boolean DEFAULT true NOT NULL,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deleted_at" timestamp with time zone,
	CONSTRAINT "ck_ai_academic_year" CHECK (((academic_year IS NULL) OR ((academic_year)::text ~ '^[0-9]{4}/[0-9]{4}$'::text))),
	CONSTRAINT "ck_ai_effective_period" CHECK (((effective_to IS NULL) OR (effective_from IS NULL) OR (effective_to >= effective_from)))
);
CREATE TABLE "ai_message_citations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"message_id" uuid NOT NULL,
	"chunk_id" uuid NOT NULL,
	"citation_order" integer NOT NULL,
	"retrieval_rank" integer,
	"relevance_score" double precision,
	"quoted_text" text,
	"document_title_snapshot" varchar(500) NOT NULL,
	"source_url_snapshot" text,
	"source_label_snapshot" varchar(255),
	"page_start_snapshot" integer,
	"page_end_snapshot" integer,
	"section_title_snapshot" varchar(500),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "uq_ai_citation_chunk" UNIQUE("message_id","chunk_id"),
	CONSTRAINT "uq_ai_citation_order" UNIQUE("message_id","citation_order"),
	CONSTRAINT "ck_ai_citation_order" CHECK ((citation_order > 0))
);
CREATE TABLE "ai_messages" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"conversation_id" uuid NOT NULL,
	"sequence_number" integer NOT NULL,
	"role" ai_message_role NOT NULL,
	"content" text NOT NULL,
	"rewritten_question" text,
	"retrieval_filters" jsonb DEFAULT '{}' NOT NULL,
	"model_name" varchar(255),
	"prompt_tokens" integer,
	"completion_tokens" integer,
	"latency_ms" integer,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "uq_ai_message_sequence" UNIQUE("conversation_id","sequence_number"),
	CONSTRAINT "ck_ai_message_sequence" CHECK ((sequence_number > 0))
);
CREATE TABLE "ai_source_urls" (
	"source_id" uuid NOT NULL,
	"canonical_url" text NOT NULL,
	"url_hash" varchar(64) NOT NULL,
	"etag" text,
	"last_modified" text,
	"content_hash" varchar(64),
	"last_http_status" integer,
	"last_checked_at" timestamp with time zone,
	"last_changed_at" timestamp with time zone,
	"document_id" uuid,
	"active" boolean DEFAULT true NOT NULL,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"id" uuid DEFAULT gen_random_uuid(),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "pk_ai_source_urls" PRIMARY KEY("id"),
	CONSTRAINT "uq_ai_source_url_hash" UNIQUE("source_id","url_hash")
);
CREATE TABLE "ai_sources" (
	"name" varchar(255) NOT NULL,
	"base_url" text NOT NULL CONSTRAINT "uq_ai_sources_base_url" UNIQUE,
	"allowed_domains" jsonb DEFAULT '[]' NOT NULL,
	"allowed_path_prefixes" jsonb DEFAULT '[]' NOT NULL,
	"document_type" ai_document_type DEFAULT 'OTHER' NOT NULL,
	"issuer" varchar(255),
	"academic_year" varchar(9),
	"enabled" boolean DEFAULT true NOT NULL,
	"schedule_minutes" integer DEFAULT 1440 NOT NULL,
	"max_depth" integer DEFAULT 3 NOT NULL,
	"max_pages_per_run" integer DEFAULT 100 NOT NULL,
	"crawl_delay_seconds" double precision DEFAULT 1 NOT NULL,
	"next_crawl_at" timestamp with time zone,
	"last_checked_at" timestamp with time zone,
	"last_success_at" timestamp with time zone,
	"consecutive_failures" integer DEFAULT 0 NOT NULL,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"id" uuid DEFAULT gen_random_uuid(),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "pk_ai_sources" PRIMARY KEY("id"),
	CONSTRAINT "ck_ai_sources_ck_ai_sources_ai_source_delay" CHECK ((crawl_delay_seconds >= (0)::double precision)),
	CONSTRAINT "ck_ai_sources_ck_ai_sources_ai_source_depth" CHECK (((max_depth >= 0) AND (max_depth <= 10))),
	CONSTRAINT "ck_ai_sources_ck_ai_sources_ai_source_page_limit" CHECK (((max_pages_per_run >= 1) AND (max_pages_per_run <= 5000))),
	CONSTRAINT "ck_ai_sources_ck_ai_sources_ai_source_schedule" CHECK ((schedule_minutes >= 15))
);
CREATE TABLE "alembic_version" (
	"version_num" varchar(32),
	CONSTRAINT "alembic_version_pkc" PRIMARY KEY("version_num")
);
CREATE TABLE "audit_logs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"actor_id" uuid,
	"action" varchar(100) NOT NULL,
	"target_type" varchar(50) NOT NULL,
	"target_id" uuid,
	"ip_address" inet,
	"metadata" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "comments" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"post_id" uuid NOT NULL,
	"user_id" uuid NOT NULL,
	"parent_id" uuid,
	"content" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deleted_at" timestamp with time zone
);
CREATE TABLE "conversation_members" (
	"conversation_id" uuid,
	"user_id" uuid,
	"joined_at" timestamp with time zone DEFAULT now() NOT NULL,
	"left_at" timestamp with time zone,
	CONSTRAINT "conversation_members_pkey" PRIMARY KEY("conversation_id","user_id")
);
CREATE TABLE "conversations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"type" conversation_type DEFAULT 'DIRECT' NOT NULL,
	"title" varchar(255),
	"created_by" uuid,
	"last_message_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "email_verification_codes" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid NOT NULL,
	"code_hash" text NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	"consumed_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "ck_email_code_expiry" CHECK ((expires_at > created_at))
);
CREATE TABLE "friend_requests" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"sender_id" uuid NOT NULL,
	"receiver_id" uuid NOT NULL,
	"status" friend_request_status DEFAULT 'PENDING' NOT NULL,
	"responded_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "ck_friend_request_distinct" CHECK ((sender_id <> receiver_id))
);
CREATE TABLE "friendships" (
	"user_low_id" uuid,
	"user_high_id" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "friendships_pkey" PRIMARY KEY("user_low_id","user_high_id"),
	CONSTRAINT "ck_friendship_order" CHECK ((user_low_id < user_high_id))
);
CREATE TABLE "group_members" (
	"group_id" uuid,
	"user_id" uuid,
	"role" group_role DEFAULT 'MEMBER' NOT NULL,
	"joined_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "group_members_pkey" PRIMARY KEY("group_id","user_id")
);
CREATE TABLE "groups" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"name" varchar(150) NOT NULL,
	"slug" varchar(160) NOT NULL CONSTRAINT "groups_slug_key" UNIQUE,
	"description" text,
	"cover_object_key" text,
	"status" group_status DEFAULT 'ACTIVE' NOT NULL,
	"created_by" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "media_files" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"owner_id" uuid,
	"bucket" varchar(100) NOT NULL,
	"object_key" text NOT NULL,
	"original_name" varchar(500),
	"mime_type" varchar(150) NOT NULL,
	"file_size" bigint NOT NULL,
	"checksum_sha256" varchar(64),
	"width" integer,
	"height" integer,
	"status" media_status DEFAULT 'PENDING' NOT NULL,
	"uploaded_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deleted_at" timestamp with time zone,
	CONSTRAINT "uq_media_object" UNIQUE("bucket","object_key"),
	CONSTRAINT "ck_media_file_size" CHECK ((file_size >= 0)),
	CONSTRAINT "ck_media_dimensions" CHECK (((width IS NULL) OR (width > 0)) AND ((height IS NULL) OR (height > 0))),
	CONSTRAINT "ck_media_ready_uploaded" CHECK (((status <> 'READY') OR (uploaded_at IS NOT NULL)))
);
CREATE TABLE "group_join_requests" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"group_id" uuid NOT NULL,
	"user_id" uuid NOT NULL,
	"status" group_join_request_status DEFAULT 'PENDING' NOT NULL,
	"reviewed_by" uuid,
	"reviewed_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "uq_group_join_request_user" UNIQUE("group_id","user_id")
);
CREATE TABLE "message_attachments" (
	"message_id" uuid,
	"media_id" uuid,
	CONSTRAINT "message_attachments_pkey" PRIMARY KEY("message_id","media_id")
);
CREATE TABLE "message_receipts" (
	"message_id" uuid,
	"user_id" uuid,
	"delivered_at" timestamp with time zone,
	"seen_at" timestamp with time zone,
	CONSTRAINT "message_receipts_pkey" PRIMARY KEY("message_id","user_id"),
	CONSTRAINT "ck_receipt_order" CHECK (((seen_at IS NULL) OR (delivered_at IS NULL) OR (seen_at >= delivered_at)))
);
CREATE TABLE "messages" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"conversation_id" uuid NOT NULL,
	"sender_id" uuid,
	"message_type" message_type DEFAULT 'TEXT' NOT NULL,
	"content" text,
	"reply_to_id" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"edited_at" timestamp with time zone,
	"deleted_at" timestamp with time zone,
	CONSTRAINT "ck_message_has_content" CHECK (((content IS NOT NULL) OR (message_type = ANY (ARRAY['IMAGE'::message_type, 'FILE'::message_type]))))
);
CREATE TABLE "notifications" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid NOT NULL,
	"type" notification_type NOT NULL,
	"title" varchar(255) NOT NULL,
	"content" text,
	"actor_id" uuid,
	"reference_type" varchar(50),
	"reference_id" uuid,
	"payload" jsonb DEFAULT '{}' NOT NULL,
	"read_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "post_likes" (
	"post_id" uuid,
	"user_id" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "post_likes_pkey" PRIMARY KEY("post_id","user_id")
);
CREATE TABLE "post_media" (
	"post_id" uuid,
	"media_id" uuid,
	"sort_order" integer DEFAULT 0 NOT NULL,
	CONSTRAINT "post_media_pkey" PRIMARY KEY("post_id","media_id"),
	CONSTRAINT "uq_post_media_order" UNIQUE("post_id","sort_order")
);
CREATE TABLE "posts" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"group_id" uuid,
	"author_id" uuid NOT NULL,
	"content" text DEFAULT '' NOT NULL,
	"category" varchar(30) DEFAULT 'general' NOT NULL,
	"post_type" post_type DEFAULT 'STANDARD' NOT NULL,
	"visibility" post_visibility DEFAULT 'PUBLIC' NOT NULL,
	"status" post_status DEFAULT 'PENDING' NOT NULL,
	"reviewed_by" uuid,
	"reviewed_at" timestamp with time zone,
	"rejection_reason" text,
	"is_pinned" boolean DEFAULT false NOT NULL,
	"search_vector" tsvector GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, COALESCE(content, ''::text))) STORED,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deleted_at" timestamp with time zone,
	CONSTRAINT "ck_posts_group_scope" CHECK (((post_type = 'STANDARD') AND (group_id IS NOT NULL)) OR ((post_type <> 'STANDARD') AND (group_id IS NULL)))
);
CREATE TABLE "profiles" (
	"user_id" uuid PRIMARY KEY,
	"student_code" varchar(50) CONSTRAINT "profiles_student_code_key" UNIQUE,
	"full_name" varchar(150) NOT NULL,
	"avatar_media_id" uuid,
	"cover_media_id" uuid,
	"bio" text,
	"faculty" varchar(150),
	"cohort" varchar(50),
	"pronouns" varchar(50),
	"workplace" varchar(150),
	"education" varchar(150),
	"current_city" varchar(150),
	"hometown" varchar(150),
	"social_links" jsonb DEFAULT '{}' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "refresh_tokens" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid NOT NULL,
	"token_hash" text NOT NULL CONSTRAINT "refresh_tokens_token_hash_key" UNIQUE,
	"expires_at" timestamp with time zone NOT NULL,
	"revoked_at" timestamp with time zone,
	"replaced_by_id" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "request_rate_limits" (
	"identifier" varchar(255) NOT NULL,
	"bucket" varchar(100) NOT NULL,
	"window_start" timestamp with time zone NOT NULL,
	"request_count" integer DEFAULT 1 NOT NULL,
	CONSTRAINT "request_rate_limits_pkey" PRIMARY KEY ("identifier", "bucket", "window_start")
);
CREATE TABLE "reports" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"reporter_id" uuid,
	"target_type" report_target_type NOT NULL,
	"target_id" uuid NOT NULL,
	"reason" text NOT NULL,
	"status" report_status DEFAULT 'PENDING' NOT NULL,
	"handled_by" uuid,
	"resolution_note" text,
	"evidence_media_id" uuid,
	"handled_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE "roles" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"code" varchar(50) NOT NULL CONSTRAINT "roles_code_key" UNIQUE,
	"description" text
);
CREATE TABLE "user_blocks" (
	"blocker_id" uuid,
	"blocked_id" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "user_blocks_pkey" PRIMARY KEY("blocker_id","blocked_id"),
	CONSTRAINT "ck_user_block_distinct" CHECK ((blocker_id <> blocked_id))
);
CREATE TABLE "user_roles" (
	"user_id" uuid,
	"role_id" uuid,
	"assigned_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "user_roles_pkey" PRIMARY KEY("user_id","role_id")
);
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"email" varchar(255) NOT NULL,
	"username" varchar(100) NOT NULL CONSTRAINT "uq_users_username" UNIQUE,
	"password_hash" text NOT NULL,
	"status" account_status DEFAULT 'PENDING' NOT NULL,
	"system_role" system_role DEFAULT 'USER' NOT NULL,
	"email_verified_at" timestamp with time zone,
	"last_login_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	"deleted_at" timestamp with time zone,
	"failed_login_attempts" integer DEFAULT 0 NOT NULL,
	"login_locked_until" timestamp with time zone,
	CONSTRAINT "ck_users_hvnh_email" CHECK ((lower((email)::text) ~ '^[^@]+@hvnh\.edu\.vn$'::text))
);
CREATE INDEX "idx_ai_conversations_user" ON "ai_conversations" ("user_id","updated_at");
CREATE INDEX "idx_ai_crawl_items_run" ON "ai_crawl_items" ("run_id","status");
CREATE INDEX "idx_ai_crawl_runs_source" ON "ai_crawl_runs" ("source_id","queued_at");
CREATE INDEX "idx_ai_crawl_runs_status" ON "ai_crawl_runs" ("status","queued_at");
CREATE INDEX "idx_ai_chunks_content_fts" ON "ai_document_chunks" USING gin (to_tsvector('simple', COALESCE("content", '')));
CREATE INDEX "idx_ai_chunks_version" ON "ai_document_chunks" ("document_version_id","chunk_index");
CREATE INDEX "idx_ai_document_relations_number" ON "ai_document_relations" ("referenced_number");
CREATE INDEX "idx_ai_document_relations_source" ON "ai_document_relations" ("source_document_version_id");
CREATE INDEX "idx_ai_document_relations_target" ON "ai_document_relations" ("target_document_id");
CREATE INDEX "idx_ai_versions_status" ON "ai_document_versions" ("status","created_at");
CREATE INDEX "idx_ai_documents_metadata" ON "ai_documents" USING gin ("metadata");
CREATE INDEX "idx_ai_documents_retrieval" ON "ai_documents" ("document_type","academic_year","is_current","published_at");
CREATE INDEX "idx_ai_citations_message" ON "ai_message_citations" ("message_id","citation_order");
CREATE INDEX "idx_ai_messages_history" ON "ai_messages" ("conversation_id","sequence_number");
CREATE INDEX "idx_ai_source_urls_document" ON "ai_source_urls" ("document_id");
CREATE INDEX "idx_ai_source_urls_source" ON "ai_source_urls" ("source_id","last_checked_at");
CREATE INDEX "idx_ai_sources_due" ON "ai_sources" ("enabled","next_crawl_at");
CREATE INDEX "idx_audit_logs_target" ON "audit_logs" ("target_type","target_id","created_at");
CREATE INDEX "idx_comments_post" ON "comments" ("post_id","created_at");
CREATE INDEX "idx_conversation_members_user" ON "conversation_members" ("user_id","conversation_id");
CREATE INDEX "idx_email_codes_user_active" ON "email_verification_codes" ("user_id","expires_at");
CREATE UNIQUE INDEX "uq_pending_friend_pair" ON "friend_requests" (LEAST("sender_id", "receiver_id"), GREATEST("sender_id", "receiver_id")) WHERE "status" = 'PENDING';
CREATE INDEX "idx_friendships_high" ON "friendships" ("user_high_id");
CREATE INDEX "idx_group_members_user" ON "group_members" ("user_id","joined_at");
CREATE INDEX "idx_media_owner_status" ON "media_files" ("owner_id","status","created_at");
CREATE INDEX "idx_messages_realtime" ON "messages" ("conversation_id","created_at");
CREATE INDEX "idx_notifications_unread" ON "notifications" ("user_id","created_at") WHERE "read_at" IS NULL;
CREATE INDEX "idx_posts_author" ON "posts" ("author_id","created_at");
CREATE INDEX "idx_posts_author_visibility" ON "posts" ("author_id","visibility","status","created_at");
CREATE INDEX "idx_posts_feed" ON "posts" ("group_id","status","created_at");
CREATE INDEX "idx_posts_feed_category" ON "posts" ("category","status","created_at");
CREATE INDEX "idx_posts_search" ON "posts" USING gin ("search_vector");
CREATE INDEX "idx_profiles_full_name_trgm" ON "profiles" USING gin ("full_name" gin_trgm_ops);
CREATE INDEX "idx_rate_limits_cleanup" ON "request_rate_limits" ("window_start");
CREATE INDEX "idx_refresh_tokens_user" ON "refresh_tokens" ("user_id","expires_at");
CREATE INDEX "idx_reports_queue" ON "reports" ("status","created_at");
CREATE UNIQUE INDEX "uq_users_email" ON "users" (lower("email"));
ALTER TABLE "ai_conversations" ADD CONSTRAINT "ai_conversations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "ai_crawl_items" ADD CONSTRAINT "fk_ai_crawl_items_document_version_id_ai_document_versions" FOREIGN KEY ("document_version_id") REFERENCES "ai_document_versions"("id") ON DELETE SET NULL;
ALTER TABLE "ai_crawl_items" ADD CONSTRAINT "fk_ai_crawl_items_run_id_ai_crawl_runs" FOREIGN KEY ("run_id") REFERENCES "ai_crawl_runs"("id") ON DELETE CASCADE;
ALTER TABLE "ai_crawl_items" ADD CONSTRAINT "fk_ai_crawl_items_source_url_id_ai_source_urls" FOREIGN KEY ("source_url_id") REFERENCES "ai_source_urls"("id") ON DELETE SET NULL;
ALTER TABLE "ai_crawl_runs" ADD CONSTRAINT "fk_ai_crawl_runs_source_id_ai_sources" FOREIGN KEY ("source_id") REFERENCES "ai_sources"("id") ON DELETE RESTRICT;
ALTER TABLE "ai_document_chunks" ADD CONSTRAINT "ai_document_chunks_document_version_id_fkey" FOREIGN KEY ("document_version_id") REFERENCES "ai_document_versions"("id") ON DELETE RESTRICT;
ALTER TABLE "ai_document_relations" ADD CONSTRAINT "fk_ai_document_relations_source_document_version_id_ai__f2e7" FOREIGN KEY ("source_document_version_id") REFERENCES "ai_document_versions"("id") ON DELETE CASCADE;
ALTER TABLE "ai_document_relations" ADD CONSTRAINT "fk_ai_document_relations_target_document_id_ai_documents" FOREIGN KEY ("target_document_id") REFERENCES "ai_documents"("id") ON DELETE SET NULL;
ALTER TABLE "ai_document_versions" ADD CONSTRAINT "ai_document_versions_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "ai_documents"("id") ON DELETE RESTRICT;
ALTER TABLE "ai_documents" ADD CONSTRAINT "ai_documents_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "groups"("id") ON DELETE SET NULL;
ALTER TABLE "ai_documents" ADD CONSTRAINT "ai_documents_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "ai_documents" ADD CONSTRAINT "fk_ai_current_version" FOREIGN KEY ("current_version_id") REFERENCES "ai_document_versions"("id") ON DELETE SET NULL;
ALTER TABLE "ai_message_citations" ADD CONSTRAINT "ai_message_citations_chunk_id_fkey" FOREIGN KEY ("chunk_id") REFERENCES "ai_document_chunks"("id") ON DELETE RESTRICT;
ALTER TABLE "ai_message_citations" ADD CONSTRAINT "ai_message_citations_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "ai_messages"("id") ON DELETE CASCADE;
ALTER TABLE "ai_messages" ADD CONSTRAINT "ai_messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "ai_conversations"("id") ON DELETE CASCADE;
ALTER TABLE "ai_source_urls" ADD CONSTRAINT "fk_ai_source_urls_document_id_ai_documents" FOREIGN KEY ("document_id") REFERENCES "ai_documents"("id") ON DELETE SET NULL;
ALTER TABLE "ai_source_urls" ADD CONSTRAINT "fk_ai_source_urls_source_id_ai_sources" FOREIGN KEY ("source_id") REFERENCES "ai_sources"("id") ON DELETE CASCADE;
ALTER TABLE "audit_logs" ADD CONSTRAINT "audit_logs_actor_id_fkey" FOREIGN KEY ("actor_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "comments" ADD CONSTRAINT "comments_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "comments"("id") ON DELETE CASCADE;
ALTER TABLE "comments" ADD CONSTRAINT "comments_post_id_fkey" FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
ALTER TABLE "comments" ADD CONSTRAINT "comments_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT;
ALTER TABLE "conversation_members" ADD CONSTRAINT "conversation_members_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversations"("id") ON DELETE CASCADE;
ALTER TABLE "conversation_members" ADD CONSTRAINT "conversation_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "conversations" ADD CONSTRAINT "conversations_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "email_verification_codes" ADD CONSTRAINT "email_verification_codes_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friend_requests" ADD CONSTRAINT "friend_requests_receiver_id_fkey" FOREIGN KEY ("receiver_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friend_requests" ADD CONSTRAINT "friend_requests_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friendships" ADD CONSTRAINT "friendships_user_high_id_fkey" FOREIGN KEY ("user_high_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friendships" ADD CONSTRAINT "friendships_user_low_id_fkey" FOREIGN KEY ("user_low_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "group_members" ADD CONSTRAINT "group_members_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "groups"("id") ON DELETE CASCADE;
ALTER TABLE "group_members" ADD CONSTRAINT "group_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "groups" ADD CONSTRAINT "groups_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "media_files" ADD CONSTRAINT "media_files_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "message_attachments" ADD CONSTRAINT "message_attachments_media_id_fkey" FOREIGN KEY ("media_id") REFERENCES "media_files"("id") ON DELETE RESTRICT;
ALTER TABLE "message_attachments" ADD CONSTRAINT "message_attachments_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "messages"("id") ON DELETE CASCADE;
ALTER TABLE "message_receipts" ADD CONSTRAINT "message_receipts_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "messages"("id") ON DELETE CASCADE;
ALTER TABLE "message_receipts" ADD CONSTRAINT "message_receipts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "messages" ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversations"("id") ON DELETE CASCADE;
ALTER TABLE "messages" ADD CONSTRAINT "messages_reply_to_id_fkey" FOREIGN KEY ("reply_to_id") REFERENCES "messages"("id") ON DELETE SET NULL;
ALTER TABLE "messages" ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_actor_id_fkey" FOREIGN KEY ("actor_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "post_likes" ADD CONSTRAINT "post_likes_post_id_fkey" FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
ALTER TABLE "post_likes" ADD CONSTRAINT "post_likes_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "post_media" ADD CONSTRAINT "post_media_media_id_fkey" FOREIGN KEY ("media_id") REFERENCES "media_files"("id") ON DELETE RESTRICT;
ALTER TABLE "post_media" ADD CONSTRAINT "post_media_post_id_fkey" FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
ALTER TABLE "posts" ADD CONSTRAINT "posts_author_id_fkey" FOREIGN KEY ("author_id") REFERENCES "users"("id") ON DELETE RESTRICT;
ALTER TABLE "posts" ADD CONSTRAINT "posts_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "groups"("id") ON DELETE CASCADE;
ALTER TABLE "posts" ADD CONSTRAINT "posts_reviewed_by_fkey" FOREIGN KEY ("reviewed_by") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_avatar_media_id_fkey" FOREIGN KEY ("avatar_media_id") REFERENCES "media_files"("id") ON DELETE SET NULL;
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_cover_media_id_fkey" FOREIGN KEY ("cover_media_id") REFERENCES "media_files"("id") ON DELETE SET NULL;
ALTER TABLE "refresh_tokens" ADD CONSTRAINT "refresh_tokens_replaced_by_id_fkey" FOREIGN KEY ("replaced_by_id") REFERENCES "refresh_tokens"("id") ON DELETE SET NULL;
ALTER TABLE "refresh_tokens" ADD CONSTRAINT "refresh_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "reports" ADD CONSTRAINT "reports_handled_by_fkey" FOREIGN KEY ("handled_by") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "reports" ADD CONSTRAINT "reports_reporter_id_fkey" FOREIGN KEY ("reporter_id") REFERENCES "users"("id") ON DELETE SET NULL;
ALTER TABLE "user_blocks" ADD CONSTRAINT "user_blocks_blocked_id_fkey" FOREIGN KEY ("blocked_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "user_blocks" ADD CONSTRAINT "user_blocks_blocker_id_fkey" FOREIGN KEY ("blocker_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "user_roles" ADD CONSTRAINT "user_roles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "roles"("id") ON DELETE CASCADE;
ALTER TABLE "user_roles" ADD CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
