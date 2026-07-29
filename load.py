import duckdb 
import pandas as pd
import pathlib 
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
from dotenv import load_dotenv
import clean
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=observatoire-sirene")
SCHEMA = pathlib.Path(__file__).resolve().parent / "schema.sql"
def connect():
    return psycopg2.connect(DATABASE_URL)
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
def load_dim_tranche_effectifs(dim_tranche_effectifs,cur):

    sql = """
                INSERT INTO dim_tranche_effectifs (
                    code_tranche, libelle
                )
                VALUES %s
                ON CONFLICT DO NOTHING
            """
    rows = dim_tranche_effectifs.values.tolist()            
    execute_values(
                cur,
                sql,
                rows,
                page_size=10000
            )

def  load_dim_activite(dim_activite,cur):
    rows = dim_activite.values.tolist()
    sql = """
            INSERT INTO dim_activite (
                code_ape, nomenclature
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


def load_fait_etablissement_version(path, cur,con):

    result = con.sql(f"""
        SELECT siret,
                        dateDebut,
                        dateFin,
                        is_current,
                        code_commune,
                        code_ape,
                        tranche_effectifs,
                        etat
        FROM read_parquet('{path}')
    """)

    rows = result.fetchall()

    con.close()

    if not rows:
        print("Aucune donnée à charger")
        return

    sql = """
        INSERT INTO fait_etablissement_version (
            siret,
            valid_from,
            valid_to,
            is_current,
            code_commune,
            code_ape,
            code_tranche,
            etat
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

    print(f"{len(rows)} lignes chargées")


    