import duckdb 
import pandas as pd
import pathlib 
import psycopg2
from psycopg2.extras import execute_values
import clean

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=observatoire-sirene")
SCHEMA = pathlib.Path(__file__).resolve().parent / "schema.sql"

def connect():
    return psycopg2.connect(DATABASE_URL)


def create_schema(cur):
    cur.execute(SCHEMA.read_text())
    
def load_commune(cur, dep):
    rows = duckdb.sql(f"""
                    SELECT insee_code, name, code_departement
                    FROM 'data/commune.parquet'
                    WHERE code_departement = '{dep}'
            """).fetchall()
    sql = """
            INSERT INTO dim_commune (
                code_commune, libelle_commune, code_departement
            )
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        
    execute_values(
        cur,
        sql,
        rows,
        page_size=10000
    )
    
def load_commune_raw(cur, duckdb_table):
    rows = (
        duckdb_table
        .project("""
            code_commune,
            libelle_commune,
            SUBSTRING(code_commune,1,2) AS code_departement
        """)
        .distinct()
        .fetchall()
    )
    sql = """
            INSERT INTO dim_commune (
                code_commune, libelle_commune, code_departement
            )
            VALUES %s
            ON CONFLICT DO NOTHING
        """
            
    execute_values(
            cur,
            sql,
            rows,
            page_size=10000
        )

def count_rows(cur, table, colone, condition_):

    cur.execute(f"SELECT count(*) FROM {table} WHERE {colone} LIKE %s", (condition_ + "%",))
    return cur.fetchone()[0]

def load_date(cur, duckdb_table):
    rows = (
        duckdb_table
        .project("""
            dateDebut
        """)
        .distinct()
        .fetchall()
    )
    sql = """
            INSERT INTO dim_date (
                date_id, annee, trimestre, mois
            )
            VALUES %s
            ON CONFLICT DO NOTHING
        """
    rows_dates = []
    for row in rows:
        date_row = clean.clean_date(row[0])
        if len(date_row) == 4:
            rows_dates.append(date_row)
    
    execute_values(
            cur,
            sql,
            rows_dates,
            page_size=10000
        )