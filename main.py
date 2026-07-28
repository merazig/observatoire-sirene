import pandas as pd
import collect
import duckdb
import quality
import sys

con = duckdb.connect()

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)


url_StockEtablissement="https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet"
url_Historique="https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet"


def main():
    
    stock, historique = collect.collect(con, url_StockEtablissement, url_Historique, 'DEPT')
    print(len(stock))
    print(len(historique))

    bornes, aberrations = quality.check_dates_aberrantes(con, historique)
    print("\n--- Bornes des dates ---")
    print(bornes.df())
    print("\n--- Dates aberrantes ---")
    print(aberrations.df())
    
if __name__== "__main__":
    main()