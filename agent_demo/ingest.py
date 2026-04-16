"""Load History_11127185.xlsx into the iot table."""

import math

import pandas as pd
from psycopg2.extras import execute_values
from tqdm import tqdm

from agent_demo.db import get_connection

XLSX_PATH = "data/History_11127185.xlsx"
SHEET_NAME = "History Stream_Download_1775687"
BATCH_SIZE = 500

COLUMN_MAP = {
    "Service_Number": "service_number",
    "Panel": "panel",
    "Local_Time": "local_time",
    "device_id": "device_id",
    "Device_Name": "device_name",
    "DeviceMapping": "device_mapping",
    "Event": "event",
    "Event_Value": "event_value",
    "Description": "description",
    "Zone": "zone",
    "Device_Type": "device_type",
    "Panel_Source": "panel_source",
    "Panel_User": "panel_user",
    "CameraEvent": "camera_event",
    "ClipName": "clip_name",
    "ClipLength": "clip_length",
    "Platform_Event_Source": "platform_event_source",
    "Platform_User": "platform_user",
    "Lock_Operation_Type": "lock_operation_type",
}

TEXT_COLS = {
    "device_name",
    "device_mapping",
    "event",
    "event_value",
    "description",
    "device_type",
    "panel_source",
    "panel_user",
    "camera_event",
    "clip_name",
    "platform_event_source",
    "platform_user",
    "lock_operation_type",
}


def _clean_row(row: pd.Series) -> tuple:
    values = []
    for col in COLUMN_MAP.values():
        v = row[col]
        if pd.isna(v):
            values.append(None)
        elif col == "zone":
            values.append(int(v))
        elif col == "clip_length":
            values.append(float(v))
        elif col in {"service_number", "panel", "device_id"}:
            values.append(int(v))
        elif col == "local_time":
            values.append(v.to_pydatetime())
        elif col in TEXT_COLS:
            values.append(str(v))
        else:
            values.append(v)
    return tuple(values)


def ingest():
    df = pd.read_excel(XLSX_PATH, sheet_name=SHEET_NAME)
    df = df.rename(columns=COLUMN_MAP)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM iot")
        count = cur.fetchone()[0]
        if count > 0:
            print(f"iot table already has {count} rows. Skipping ingest.")
            conn.close()
            return

    cols = list(COLUMN_MAP.values())
    insert_sql = f"INSERT INTO iot ({', '.join(cols)}) VALUES %s"

    num_batches = math.ceil(len(df) / BATCH_SIZE)
    for start in tqdm(range(0, len(df), BATCH_SIZE), total=num_batches, desc="Inserting"):
        batch = df.iloc[start : start + BATCH_SIZE]
        rows = [_clean_row(r) for _, r in batch.iterrows()]
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, rows)
        conn.commit()

    conn.close()
    print(f"Ingest complete: inserted {len(df)} rows into iot.")


if __name__ == "__main__":
    ingest()
