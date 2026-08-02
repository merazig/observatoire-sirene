import collect
import duckdb
import load_alt
import sys
import time
import load
import clean

con = duckdb.connect()
#con.execute("SET http_timeout=300;")  # 5 minutes
DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

#url_StockEtablissement='C:/Users/PC/Downloads/stock-stocketablissement-parquet.parquet'
#url_Historique='C:/Users/PC/Downloads/stock-stocketablissementhistorique-parquet.parquet'

url_StockEtablissement="local_data/stock-stocketablissement-parquet.parquet"
url_Historique="local_data/stock-stocketablissementhistorique-parquet.parquet"

def main():
        
    try:
        conn = load_alt.connect()
        print("Connexion OK")
    except Exception as e:
        print(f"Problème de connexion : {e}")
        raise
    
    conn.autocommit = True
    cur = conn.cursor()
    
    load_alt.create_schema(cur)
    
    print(f"======= Departement {DEPT} =======")
    
    time_start = time.perf_counter()
    stock_histoire = collect.collect_alt(con, url_StockEtablissement, url_Historique, DEPT)
    print("temps de collect:", round((time.perf_counter() - time_start),3))
    
    
    time_start = time.perf_counter()
    dim_tranche_effectifs = clean.construire_dim_tranche_effectifs()
    load.load_dim_tranche_effectifs(dim_tranche_effectifs, cur)
    load_alt.load_all(cur, stock_histoire, 100000)
    print("temps de clean et load:", round((time.perf_counter() - time_start),3))
    
    count = load.count_rows(cur, "dim_commune", "code_departement", DEPT)
    print(f"Communes: {count}")
        
    count = load.count_rows(cur, "fait_etablissement_version", "code_commune", DEPT)
    print(f"Versions: {count}")    
    conn.close()
            
if __name__== "__main__":
    main()