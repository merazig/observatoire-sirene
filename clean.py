import duckdb
import collect

url_StockEtablissement = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093629/stock-stocketablissement-parquet.parquet"
url_Historique = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20260701-093717/stock-stocketablissementhistorique-parquet.parquet"
con = duckdb.connect()
stock, historique = collect.collect(con,url_StockEtablissement, url_Historique, "69")

def clean_dim_commune(con, stock):
    commune = con.sql("""
        SELECT
            code_commune,
            MAX(libelle_commune) AS libelle_commune,
            SUBSTRING(code_commune, 1, 2) AS code_departement
        FROM stock
        WHERE code_commune IS NOT NULL
        GROUP BY code_commune
        ORDER BY code_commune
    """)
    return commune



if __name__ == "__main__":

    commune = clean_dim_commune(con,stock)
    print(commune.df().head())
    print(commune.df().info())