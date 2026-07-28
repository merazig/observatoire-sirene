import duckdb 
import pandas as pd
import pathlib 
import psycopg2

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=observatoire_sirene")
SCHEMA = pathlib.Path(__file__).resolve().parent / "schema.sql"

def connect():
    return psycopg2.connect(DATABASE_URL)


def create_schema(cur):
    cur.execute(SCHEMA.read_text())
    
def load_commune(cur):
    rows = duckdb.sql("""
                    SELECT insee_code, name, code_departement
                    FROM 'data/commune.parquet'
               """).fetchall()
    sql = """
            INSERT INTO dim_commune (
                code_commune, libelle_commune, code_departement
            )
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        
    cur.execute_values(
        sql,
        rows,
        page_size=10000
    )
    
