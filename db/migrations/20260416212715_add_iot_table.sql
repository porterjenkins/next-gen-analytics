-- Create "iot" table
CREATE TABLE "iot" (
  "id" serial NOT NULL,
  "service_number" bigint NOT NULL,
  "panel" bigint NOT NULL,
  "local_time" timestamp NOT NULL,
  "device_id" bigint NOT NULL,
  "device_name" text NULL,
  "device_mapping" text NULL,
  "event" text NULL,
  "event_value" text NULL,
  "description" text NULL,
  "zone" integer NULL,
  "device_type" text NULL,
  "panel_source" text NULL,
  "panel_user" text NULL,
  "camera_event" text NULL,
  "clip_name" text NULL,
  "clip_length" real NULL,
  "platform_event_source" text NULL,
  "platform_user" text NULL,
  "lock_operation_type" text NULL,
  PRIMARY KEY ("id")
);
