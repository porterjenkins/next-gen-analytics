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
  column "embedding" {
    type = sql("vector(384)")
    null = true
  }

  primary_key {
    columns = [column.id]
  }
}
