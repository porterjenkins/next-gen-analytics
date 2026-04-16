extension "vector" {
  schema = schema.public
}

schema "public" {
}

table "field_notes" {
  schema = schema.public

  column "id" {
    type = serial
    null = false
  }
  column "created_at" {
    type    = timestamptz
    null    = false
  }
  column "document_text" {
    type = text
    null = false
  }

  primary_key {
    columns = [column.id]
  }
}

table "iot" {
  schema = schema.public

  column "id" {
    type = serial
    null = false
  }
  column "service_number" {
    type = bigint
    null = false
  }
  column "panel" {
    type = bigint
    null = false
  }
  column "local_time" {
    type = timestamp
    null = false
  }
  column "device_id" {
    type = bigint
    null = false
  }
  column "device_name" {
    type = text
    null = true
  }
  column "device_mapping" {
    type = text
    null = true
  }
  column "event" {
    type = text
    null = true
  }
  column "event_value" {
    type = text
    null = true
  }
  column "description" {
    type = text
    null = true
  }
  column "zone" {
    type = integer
    null = true
  }
  column "device_type" {
    type = text
    null = true
  }
  column "panel_source" {
    type = text
    null = true
  }
  column "panel_user" {
    type = text
    null = true
  }
  column "camera_event" {
    type = text
    null = true
  }
  column "clip_name" {
    type = text
    null = true
  }
  column "clip_length" {
    type = real
    null = true
  }
  column "platform_event_source" {
    type = text
    null = true
  }
  column "platform_user" {
    type = text
    null = true
  }
  column "lock_operation_type" {
    type = text
    null = true
  }

  primary_key {
    columns = [column.id]
  }
}

table "notes" {
  schema = schema.public

  column "id" {
    type = serial
    null = false
  }
  column "datetime" {
    type    = timestamptz
    null    = false
  }
  column "text" {
    type = text
    null = false
  }
  column "city" {
    type = text
    null = false
  }
  column "embedding" {
    type = sql("vector(384)")
    null = true
  }

  primary_key {
    columns = [column.id]
  }
}
