-- CreateTable
CREATE TABLE "user_memories" (
    "id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "key" VARCHAR(100) NOT NULL,
    "value" TEXT NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "source" VARCHAR(200),
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_memories_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "channel_user_mappings" (
    "id" UUID NOT NULL,
    "channel" VARCHAR(30) NOT NULL,
    "channel_user_id" VARCHAR(200) NOT NULL,
    "user_id" UUID NOT NULL,
    "display_name" VARCHAR(100),
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "channel_user_mappings_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "user_memories_user_id_idx" ON "user_memories"("user_id");

-- CreateIndex
CREATE UNIQUE INDEX "user_memories_user_id_key_key" ON "user_memories"("user_id", "key");

-- CreateIndex
CREATE INDEX "channel_user_mappings_user_id_idx" ON "channel_user_mappings"("user_id");

-- CreateIndex
CREATE UNIQUE INDEX "channel_user_mappings_channel_channel_user_id_key" ON "channel_user_mappings"("channel", "channel_user_id");
