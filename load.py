import pandas as pd
import duckdb
from sqlalchemy import create_engine
import psycopg2

DATABASE_URL = "postgresql+psycopg2://postgres:admin@localhost:5432/megabase0"
engine = create_engine(DATABASE_URL)

duck = duckdb.connect()

conn = psycopg2.connect(DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"))
conn.autocommit = False
cur = conn.cursor()
date_min = "2021-01-01"
date_max = "2023-01-01"


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
        if_exists="append",
        index=False,
        method="multi"
    )

    print("Dimension date créée ")


if __name__ == "__main__":
    construire_dim_date()