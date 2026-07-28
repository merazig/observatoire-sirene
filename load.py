from pandas import pd
import duckdb
import os
import pathlib
import psycopg2

DB_URL = os.environ.get("DATABASE_URL", "dbname=observatoire-sirene")
SCHEMA = pathlib.Path(__file__).resolve().parent / "schema.sql"


def connect():
    return psycopg2.connect(DB_URL)


def create_schema(cur):
    cur.execute(SCHEMA.read_text())



