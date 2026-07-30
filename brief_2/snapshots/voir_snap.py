import duckdb
con = duckdb.connect("entrepot.duckdb")
print(con.sql("SELECT siret, etat, code_ape, dbt_valid_from, dbt_valid_to FROM snap_etat ORDER BY siret, dbt_valid_from").df())