import pandas as pd
import collect
import duckdb
import quality
import load
import sys
import time

con = duckdb.connect()

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)


url_StockEtablissement="local_data/stock-stocketablissement-parquet.parquet"
url_Historique="local_data/stock-stocketablissementhistorique-parquet.parquet"


def main():
    
    time_start = time.time()
    try:
        conn = load.connect()
        print("Connexion OK")
    except Exception as e:
        print(f"Problème de connexion : {e}")
        raise
    
    cur = conn.cursor()
    
    load.create_schema(cur)
    
    print(f"======= Departement {DEPT} =======")
    
    stock, historique = collect.collect(con, url_StockEtablissement, url_Historique, DEPT)
    print(f"siret_stock: {len(stock)}")
    print(f"siret_fin: {len(historique)}")
    
    load.load_commune_raw(cur, stock)
    
    load.load_date(cur, historique)
    conn.commit()
    
    count = load.count_rows(cur, "dim_commune", "code_departement", DEPT)
    print(f"Communes: {count}")
    cur.execute("SELECT COUNT(*) FROM dim_date")
    count = cur.fetchone()[0]
    print(f"Dates totale: {count}")
    conn.close()
    
    print("temps:", round((time.time() - time_start),3))

if __name__== "__main__":
    main()