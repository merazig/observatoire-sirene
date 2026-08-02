import collect
import duckdb
import load
import sys
import time
import clean
from datetime import datetime


con = duckdb.connect()
#con.execute("SET http_timeout=300;")  # 5 minutes
DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

#url_StockEtablissement='C:/Users/PC/Downloads/stock-stocketablissement-parquet.parquet'
#url_Historique='C:/Users/PC/Downloads/stock-stocketablissementhistorique-parquet.parquet'

url_StockEtablissement="local_data/stock-stocketablissement-parquet.parquet"
url_Historique="local_data/stock-stocketablissementhistorique-parquet.parquet"

date_min = "1900-01-01"
date_max = str(datetime.today())

def main():
    
    try:
        conn = load.connect()
        print("Connexion OK")
    except Exception as e:
        print(f"Problème de connexion : {e}")
        raise
    
    conn.autocommit = True
    cur = conn.cursor()
    
    load.create_schema(cur)
    
    print(f"======= Departement {DEPT} =======")
    
    time_start = time.perf_counter()
    stock, historique = collect.collect(con, url_StockEtablissement, url_Historique, DEPT)
    print("temps de collect:", round((time.perf_counter() - time_start),3))

    print(f"siret_stock: {len(stock)}")
    print(f"siret_fin: {len(historique)}")
    #dim_date=clean.creer_dim_date(date_min, date_max)
    
    time_start = time.perf_counter()
    dim_activite=clean.dim_activite(con, historique)
    load.load_dim_activite(dim_activite,cur)
    dim_tranche_effectifs=clean.construire_dim_tranche_effectifs()
    load.load_dim_tranche_effectifs(dim_tranche_effectifs,cur)
    load.load_commune_raw(cur, stock)
    load.load_date(cur, historique)
    fait_etablissement=clean.fait_etablissement(stock,historique,DEPT)
    load.load_fait_etablissement_version(fait_etablissement,cur,con)
    print("temps de clean et load:", round((time.perf_counter() - time_start),3))
    #conn.commit()
        
    count = load.count_rows(cur, "dim_commune", "code_departement", DEPT)
    print(f"Communes: {count}")
    
    count = load.count_rows(cur, "fait_etablissement_version", "code_commune", DEPT)
    print(f"Versions: {count}")
    
    conn.close()
    

if __name__== "__main__":
    main()