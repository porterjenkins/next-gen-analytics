-- Create "field_notes" table
CREATE TABLE "field_notes" (
  "id" serial NOT NULL,
  "created_at" timestamptz NOT NULL,
  "document_text" text NOT NULL,
  PRIMARY KEY ("id")
);
-- Create "notes" table
CREATE TABLE "notes" (
  "id" serial NOT NULL,
  "datetime" timestamptz NOT NULL,
  "text" text NOT NULL,
  "embedding" vector(384) NULL,
  PRIMARY KEY ("id")
);
