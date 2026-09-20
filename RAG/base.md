CREATE SCHEMA "public";
CREATE TYPE "post_status" AS ENUM('PENDING', 'APPROVED', 'REJECTED');
CREATE TYPE "friend_status" AS ENUM('PENDING', 'ACCEPTED', 'REJECTED');
CREATE TYPE "message_status" AS ENUM('SENT', 'DELIVERED', 'SEEN');
CREATE TABLE "ai_document_chunks" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"document_id" uuid,
	"chunk_index" integer,
	"content" text NOT NULL,
	"page_number" integer,
	"metadata" jsonb,
	"qdrant_point_id" varchar(255),
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "ai_documents" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"title" varchar(255) NOT NULL,
	"source_type" varchar(50),
	"source_url" text,
	"file_path" text,
	"status" varchar(30) DEFAULT 'ACTIVE',
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "audit_logs" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"action" varchar(100),
	"target_type" varchar(50),
	"target_id" uuid,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "comments" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"post_id" uuid,
	"user_id" uuid,
	"content" text NOT NULL,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	"deleted_at" timestamp
);
CREATE TABLE "conversation_members" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"conversation_id" uuid,
	"user_id" uuid,
	CONSTRAINT "conversation_members_conversation_id_user_id_key" UNIQUE("conversation_id","user_id")
);
CREATE TABLE "conversations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"type" varchar(30) DEFAULT 'DIRECT',
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "friend_requests" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"sender_id" uuid,
	"receiver_id" uuid,
	"status" friend_status DEFAULT 'PENDING',
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "friend_requests_sender_id_receiver_id_key" UNIQUE("sender_id","receiver_id")
);
CREATE TABLE "friendships" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"friend_id" uuid,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "friendships_user_id_friend_id_key" UNIQUE("user_id","friend_id"),
	CONSTRAINT "friendships_check" CHECK ((user_id <> friend_id))
);
CREATE TABLE "group_members" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"group_id" uuid,
	"user_id" uuid,
	"role" varchar(30) DEFAULT 'MEMBER',
	"joined_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "group_members_group_id_user_id_key" UNIQUE("group_id","user_id")
);
CREATE TABLE "groups" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"name" varchar(150) NOT NULL,
	"description" text,
	"cover_image" text,
	"status" varchar(30) DEFAULT 'ACTIVE',
	"created_by" uuid,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "media_files" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"owner_id" uuid,
	"object_key" text NOT NULL,
	"bucket" varchar(100),
	"file_type" varchar(50),
	"file_size" bigint,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "message_attachments" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"message_id" uuid,
	"object_key" text NOT NULL,
	"file_type" varchar(50),
	"file_size" bigint,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "messages" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"conversation_id" uuid,
	"sender_id" uuid,
	"content" text,
	"message_type" varchar(30) DEFAULT 'TEXT',
	"status" message_status DEFAULT 'SENT',
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	"seen_at" timestamp
);
CREATE TABLE "notifications" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"type" varchar(50),
	"title" varchar(255),
	"content" text,
	"reference_id" uuid,
	"is_read" boolean DEFAULT false,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "otp_codes" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"otp_code" varchar(20) NOT NULL,
	"expired_at" timestamp NOT NULL,
	"is_used" boolean DEFAULT false,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "post_likes" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"post_id" uuid,
	"user_id" uuid,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "post_likes_post_id_user_id_key" UNIQUE("post_id","user_id")
);
CREATE TABLE "post_media" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"post_id" uuid,
	"object_key" text NOT NULL,
	"media_type" varchar(30),
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "posts" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"group_id" uuid,
	"author_id" uuid,
	"content" text,
	"status" post_status DEFAULT 'PENDING',
	"search_vector" tsvector,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	"updated_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	"deleted_at" timestamp
);
CREATE TABLE "profiles" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid CONSTRAINT "profiles_user_id_key" UNIQUE,
	"student_code" varchar(50) CONSTRAINT "profiles_student_code_key" UNIQUE,
	"full_name" varchar(150),
	"avatar_url" text,
	"bio" text,
	"faculty" varchar(150),
	"course" varchar(50),
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "refresh_tokens" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"token" text NOT NULL,
	"expired_at" timestamp NOT NULL,
	"revoked" boolean DEFAULT false,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "reports" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"reporter_id" uuid,
	"target_type" varchar(50),
	"target_id" uuid,
	"reason" text,
	"status" varchar(30) DEFAULT 'PENDING',
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "roles" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"name" varchar(50) NOT NULL CONSTRAINT "roles_name_key" UNIQUE,
	"description" text
);
CREATE TABLE "system_settings" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"key" varchar(100) CONSTRAINT "system_settings_key_key" UNIQUE,
	"value" text,
	"description" text,
	"updated_at" timestamp DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE "user_blocks" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"blocker_id" uuid,
	"blocked_id" uuid,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "user_blocks_check" CHECK ((blocker_id <> blocked_id))
);
CREATE TABLE "user_roles" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"user_id" uuid,
	"role_id" uuid,
	CONSTRAINT "user_roles_user_id_role_id_key" UNIQUE("user_id","role_id")
);
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	"email" varchar(255) NOT NULL CONSTRAINT "users_email_key" UNIQUE,
	"username" varchar(100) NOT NULL CONSTRAINT "users_username_key" UNIQUE,
	"password_hash" text NOT NULL,
	"is_email_verified" boolean DEFAULT false,
	"is_locked" boolean DEFAULT false,
	"last_login_at" timestamp,
	"created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	"updated_at" timestamp DEFAULT CURRENT_TIMESTAMP,
	"deleted_at" timestamp
);
CREATE UNIQUE INDEX "ai_document_chunks_pkey" ON "ai_document_chunks" ("id");
CREATE INDEX "idx_ai_qdrant" ON "ai_document_chunks" ("qdrant_point_id");
CREATE UNIQUE INDEX "ai_documents_pkey" ON "ai_documents" ("id");
CREATE UNIQUE INDEX "audit_logs_pkey" ON "audit_logs" ("id");
CREATE UNIQUE INDEX "comments_pkey" ON "comments" ("id");
CREATE UNIQUE INDEX "conversation_members_conversation_id_user_id_key" ON "conversation_members" ("conversation_id","user_id");
CREATE UNIQUE INDEX "conversation_members_pkey" ON "conversation_members" ("id");
CREATE UNIQUE INDEX "conversations_pkey" ON "conversations" ("id");
CREATE UNIQUE INDEX "friend_requests_pkey" ON "friend_requests" ("id");
CREATE UNIQUE INDEX "friend_requests_sender_id_receiver_id_key" ON "friend_requests" ("sender_id","receiver_id");
CREATE UNIQUE INDEX "friendships_pkey" ON "friendships" ("id");
CREATE UNIQUE INDEX "friendships_user_id_friend_id_key" ON "friendships" ("user_id","friend_id");
CREATE UNIQUE INDEX "group_members_group_id_user_id_key" ON "group_members" ("group_id","user_id");
CREATE UNIQUE INDEX "group_members_pkey" ON "group_members" ("id");
CREATE UNIQUE INDEX "groups_pkey" ON "groups" ("id");
CREATE UNIQUE INDEX "media_files_pkey" ON "media_files" ("id");
CREATE UNIQUE INDEX "message_attachments_pkey" ON "message_attachments" ("id");
CREATE INDEX "idx_messages_realtime" ON "messages" ("conversation_id","created_at");
CREATE UNIQUE INDEX "messages_pkey" ON "messages" ("id");
CREATE INDEX "idx_notifications" ON "notifications" ("user_id","is_read","created_at");
CREATE UNIQUE INDEX "notifications_pkey" ON "notifications" ("id");
CREATE UNIQUE INDEX "otp_codes_pkey" ON "otp_codes" ("id");
CREATE UNIQUE INDEX "post_likes_pkey" ON "post_likes" ("id");
CREATE UNIQUE INDEX "post_likes_post_id_user_id_key" ON "post_likes" ("post_id","user_id");
CREATE UNIQUE INDEX "post_media_pkey" ON "post_media" ("id");
CREATE INDEX "idx_posts_feed" ON "posts" ("group_id","status","created_at");
CREATE INDEX "idx_posts_search" ON "posts" USING gin ("search_vector");
CREATE UNIQUE INDEX "posts_pkey" ON "posts" ("id");
CREATE INDEX "idx_profile_search" ON "profiles" USING gin ("full_name");
CREATE INDEX "idx_profile_student_code" ON "profiles" ("student_code");
CREATE UNIQUE INDEX "profiles_pkey" ON "profiles" ("id");
CREATE UNIQUE INDEX "profiles_student_code_key" ON "profiles" ("student_code");
CREATE UNIQUE INDEX "profiles_user_id_key" ON "profiles" ("user_id");
CREATE UNIQUE INDEX "refresh_tokens_pkey" ON "refresh_tokens" ("id");
CREATE UNIQUE INDEX "reports_pkey" ON "reports" ("id");
CREATE UNIQUE INDEX "roles_name_key" ON "roles" ("name");
CREATE UNIQUE INDEX "roles_pkey" ON "roles" ("id");
CREATE UNIQUE INDEX "system_settings_key_key" ON "system_settings" ("key");
CREATE UNIQUE INDEX "system_settings_pkey" ON "system_settings" ("id");
CREATE UNIQUE INDEX "user_blocks_pkey" ON "user_blocks" ("id");
CREATE UNIQUE INDEX "user_roles_pkey" ON "user_roles" ("id");
CREATE UNIQUE INDEX "user_roles_user_id_role_id_key" ON "user_roles" ("user_id","role_id");
CREATE INDEX "idx_users_email" ON "users" ("email");
CREATE INDEX "idx_users_username" ON "users" ("username");
CREATE UNIQUE INDEX "users_email_key" ON "users" ("email");
CREATE UNIQUE INDEX "users_pkey" ON "users" ("id");
CREATE UNIQUE INDEX "users_username_key" ON "users" ("username");
ALTER TABLE "ai_document_chunks" ADD CONSTRAINT "ai_document_chunks_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "ai_documents"("id") ON DELETE CASCADE;
ALTER TABLE "audit_logs" ADD CONSTRAINT "audit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id");
ALTER TABLE "comments" ADD CONSTRAINT "comments_post_id_fkey" FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
ALTER TABLE "comments" ADD CONSTRAINT "comments_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "conversation_members" ADD CONSTRAINT "conversation_members_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversations"("id") ON DELETE CASCADE;
ALTER TABLE "conversation_members" ADD CONSTRAINT "conversation_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friend_requests" ADD CONSTRAINT "friend_requests_receiver_id_fkey" FOREIGN KEY ("receiver_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friend_requests" ADD CONSTRAINT "friend_requests_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friendships" ADD CONSTRAINT "friendships_friend_id_fkey" FOREIGN KEY ("friend_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "friendships" ADD CONSTRAINT "friendships_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "group_members" ADD CONSTRAINT "group_members_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "groups"("id") ON DELETE CASCADE;
ALTER TABLE "group_members" ADD CONSTRAINT "group_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "groups" ADD CONSTRAINT "groups_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "users"("id");
ALTER TABLE "media_files" ADD CONSTRAINT "media_files_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "users"("id");
ALTER TABLE "message_attachments" ADD CONSTRAINT "message_attachments_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "messages"("id") ON DELETE CASCADE;
ALTER TABLE "messages" ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversations"("id") ON DELETE CASCADE;
ALTER TABLE "messages" ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "otp_codes" ADD CONSTRAINT "otp_codes_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "post_likes" ADD CONSTRAINT "post_likes_post_id_fkey" FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
ALTER TABLE "post_likes" ADD CONSTRAINT "post_likes_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "post_media" ADD CONSTRAINT "post_media_post_id_fkey" FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
ALTER TABLE "posts" ADD CONSTRAINT "posts_author_id_fkey" FOREIGN KEY ("author_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "posts" ADD CONSTRAINT "posts_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "groups"("id") ON DELETE CASCADE;
ALTER TABLE "profiles" ADD CONSTRAINT "profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "refresh_tokens" ADD CONSTRAINT "refresh_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "reports" ADD CONSTRAINT "reports_reporter_id_fkey" FOREIGN KEY ("reporter_id") REFERENCES "users"("id");
ALTER TABLE "user_blocks" ADD CONSTRAINT "user_blocks_blocked_id_fkey" FOREIGN KEY ("blocked_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "user_blocks" ADD CONSTRAINT "user_blocks_blocker_id_fkey" FOREIGN KEY ("blocker_id") REFERENCES "users"("id") ON DELETE CASCADE;
ALTER TABLE "user_roles" ADD CONSTRAINT "user_roles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "roles"("id") ON DELETE CASCADE;
ALTER TABLE "user_roles" ADD CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE;
