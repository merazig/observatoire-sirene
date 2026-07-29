import duckdb
import collect

url_StockEtablissement = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet"
url_Historique = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet"
con = duckdb.connect()
stock, historique = collect.collect(con,url_StockEtablissement, url_Historique, "69")

def clean_dim_commune(con,stock):
    # En utilisant duckdb.sql au lieu d'une connexion isolée con,
    # DuckDB retrouve automatiquement la variable 'stock'
    commune = duckdb.sql("""
        SELECT DISTINCT ON (code_commune)
            code_commune,
            MAX(libelle_commune),
            SUBSTRING(code_commune, 1, 2) AS code_departement
        FROM stock
    """)
    return commune



if name == "main":

    commune = clean_dim_commune(con,stock)
    print(commune.df().head())
    print(commune.df().info())