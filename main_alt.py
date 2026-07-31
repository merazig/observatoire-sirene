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
    time_start = time.time()
        
    try:
        conn = load_alt.connect()
        print("Connexion OK")
    except Exception as e:
        print(f"Problème de connexion : {e}")
        raise
    
    cur = conn.cursor()
    
    load_alt.create_schema(cur)
    
    print(f"======= Departement {DEPT} =======")
    stock_histoire = collect.collect_alt(con, url_StockEtablissement, url_Historique, DEPT)
    
    dim_tranche_effectifs = clean.construire_dim_tranche_effectifs()
    load.load_dim_tranche_effectifs(dim_tranche_effectifs, cur)
    load_alt.load_all(cur, stock_histoire, 100000)
    
    conn.commit()
    count = load.count_rows(cur, "dim_commune", "code_departement", DEPT)
    print(f"Communes: {count}")
        
    count = load.count_rows(cur, "fait_etablissement_version", "code_commune", DEPT)
    print(f"Versions: {count}")    
    conn.close()
        
    print("temps:", round((time.time() - time_start),3))
    
if __name__== "__main__":
    main()