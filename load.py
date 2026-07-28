import pandas as pd
import duckdb
from sqlalchemy import create_engine
import psycopg2
from datetime import date

DATABASE_URL = "postgresql+psycopg2://postgres:admin@localhost:5432/megabase0"
engine = create_engine(DATABASE_URL)

duck = duckdb.connect()

conn = psycopg2.connect(DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"))
conn.autocommit = False
cur = conn.cursor()
date_min = "1900-01-01"
date_max =  str(date.today())


def creer_dim_date(date_min, date_max):
    dates = pd.date_range(date_min, date_max, freq="D")

    return pd.DataFrame({
        "date_id": dates.date,
        "annee": dates.year,
        "trimestre": dates.quarter,
        "mois": dates.month,
    })


def construire_dim_date():
    donnees = creer_dim_date(date_min, date_max)

    duck.register("donnees", donnees)

    print(duck.sql("SELECT * FROM donnees LIMIT 5").df())


    donnees.to_sql(
        name="dim_date",
        schema="entrepot",
        con=engine,
        if_exists="delete_rows",
        index=False,
        method="multi"
    )

    print("Dimension date créée ")

def construire_dim_tranche_effectifs():
  
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

    donnees = pd.DataFrame({
        "code_tranche": list(tranches.keys()),
        "libelle": list(tranches.values()),
    })

    donnees.to_sql(
        name="dim_tranche_effectifs",
        schema="entrepot",
        con=engine,
        if_exists="delete_rows",
        index=False,
        method="multi"
    )

    print("Dimension tranche effectifss")


    
if __name__ == "__main__":
    construire_dim_date()
    construire_dim_tranche_effectifs()