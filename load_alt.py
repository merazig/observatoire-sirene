import pathlib 
import psycopg2
from psycopg2.extras import execute_values
import datetime
import os
from dotenv import load_dotenv
import clean

import io
import csv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=observatoire-sirene")
SCHEMA = pathlib.Path(__file__).resolve().parent / "schema.sql"

tranches = {
    "NN": "non renseigné",
    "00": "0 salarié",
    "01": "1-2",
    "02": "3-5",
    "03": "6-9",
    "11": "10-19",
    "12": "20-49",
    "21": "50-99",
    "22": "100-199",
    "31": "200-249",
    "32": "250-499",
    "41": "500-999",
    "42": "1000-1999",
    "51": "2000-4999",
    "52": "5000-9999",
    "53": "10000+",
}

def connect():
    return psycopg2.connect(DATABASE_URL)

def create_schema(cur):
    cur.execute(SCHEMA.read_text())
    
def load_all(cur, duckdb_rows, chunk):
    
    today = datetime.date.today()
    date_start = datetime.date(1900, 1, 1)
    cle_prec = None
    
    while True:
        
        rows = duckdb_rows.fetchmany(chunk)
        
        if not rows:
            break
    
        activite = set()
        communes = set()
        dates = set()
        versions = set()

        for row in rows:
            (
                siret,
                code_commune,
                code_tranche,
                libelle_commune,
                valid_from,
                valid_to,
                etat,
                code_ape,
                nomenclature,
            ) = row

            # filtre date
            if (
                not isinstance(valid_from, datetime.date)
                or valid_from < date_start
                or valid_from > today
            ):
                continue

            # filtre activité
            etat = etat or "?"
            code_ape = code_ape or "?"

            cle = (siret, code_ape, etat)
            if cle == cle_prec:
                continue
            cle_prec = cle

            # dim_activite
            nomenclature = nomenclature or "?"
            activite.add((code_ape, nomenclature))

            # dim_commune
            if len(code_commune) != 5:
                code_commune = "99999"
            communes.add((code_commune, libelle_commune, code_commune[:2]))

            # dim_date
            dates.add(clean.clean_date(valid_from))

            # dim_versions
            if code_tranche not in tranches:
                code_tranche = "NN"

            is_current = valid_to is None
            if valid_to is not None:
                valid_to += datetime.timedelta(days=1)

            versions.add(
                (
                    siret,
                    valid_from,
                    valid_to,
                    is_current,
                    code_commune,
                    code_ape,
                    code_tranche,
                    etat,
                )
            )
            
        dates = list(dates)
        sql = """
                    INSERT INTO dim_date (
                        date_id, annee, trimestre, mois
                    )
                    VALUES %s
                    ON CONFLICT DO NOTHING
                """
        execute_values(
                    cur,
                    sql,
                    dates,
                    page_size=50000
                )
        communes = list(communes)
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
                communes,
                page_size=50000
            )
        activite = list(activite)
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
            activite,
            page_size=50000
        )
        
        versions = list(versions)
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
            versions,
            page_size=50000
        )
        

def load_all_project(cur, duckdb_rows):
    
    today = datetime.date.today()
    date_start = datetime.date(1900, 1, 1)
    cle_prec = None
            
    rows = duckdb_rows.project("""
                       siret,
                       code_commune,
                       tranche_effectifs,
                       libelle_commune,
                       dateDebut,
                       dateFin,
                       etat,
                       code_ape,
                       nomenclature_ape
                       """).fetchall()
    

    activite = set()
    communes = set()
    dates = set()
    versions = set()

    for row in rows:
        (
            siret,
            code_commune,
            code_tranche,
            libelle_commune,
            valid_from,
            valid_to,
            etat,
            code_ape,
            nomenclature,
        ) = row

        # filtre date
        if (
            not isinstance(valid_from, datetime.date)
            or valid_from < date_start
            or valid_from > today
        ):
            continue

        # filtre activité
        etat = etat or "?"
        code_ape = code_ape or "?"

        cle = (code_ape, etat)
        if cle == cle_prec:
            continue
        cle_prec = cle

        # dim_activite
        nomenclature = nomenclature or "?"
        activite.add((code_ape, nomenclature))

        # dim_commune
        if len(code_commune) != 5:
            code_commune = "99999"
        communes.add((code_commune, libelle_commune, code_commune[:2]))

        # dim_date
        dates.add(clean.clean_date(valid_from))

        # dim_versions
        if code_tranche not in tranches:
            code_tranche = "NN"

        is_current = valid_to is None
        if valid_to is not None:
            valid_to += datetime.timedelta(days=1)

        versions.add(
            (
                siret,
                valid_from,
                valid_to,
                is_current,
                code_commune,
                code_ape,
                code_tranche,
                etat,
            )
        )
        
    dates = list(dates)
    sql = """
                INSERT INTO dim_date (
                    date_id, annee, trimestre, mois
                )
                VALUES %s
                ON CONFLICT DO NOTHING
            """
    execute_values(
                cur,
                sql,
                dates,
                page_size=50000
            )
    communes = list(communes)
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
            communes,
            page_size=50000
        )
    activite = list(activite)
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
        activite,
        page_size=50000
    )
    
    versions = list(versions)
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
        versions,
        page_size=50000
    )