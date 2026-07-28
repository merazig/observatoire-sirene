import duckdb
import collect
from datetime import date
import pandas as pd
url_StockEtablissement = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet"
url_Historique = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet"
con = duckdb.connect()
stock, historique = collect.collect(con,url_StockEtablissement, url_Historique, "69")
date_min = "1900-01-01"
date_max =  str(date.today())

def clean_dates_aberrantes(df, colonnes_dates):
    ss = pd.Series(True, index=df.index)
    for col in colonnes_dates:
        valide = df[col].isna() | df[col].between(date_min, date_max)
        ss &= valide
    return df[ss]
 
 
if __name__ == "__main__":
    stock, historique = collect.collect(con, url_StockEtablissement, url_Historique, "69")
    historique_propre = clean_dates_aberrantes(historique.df(), ["dateDebut", "dateFin"])
    print(f"{len(historique_propre)} lignes valides sur {len(historique.df())}")



