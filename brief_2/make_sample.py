import os

import duckdb

COMMUNE = "69384"   

DOSSIER = r"C:\Users\Utilisateur\Documents"
url_stock = os.path.join(DOSSIER, "stock-stocketablissement-parquet (1).parquet")
url_hist  = os.path.join(DOSSIER, "stock-stocketablissementhistorique-parquet.parquet")


con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

con.execute(f"""
    COPY (
        SELECT
            h.siret,
            h.dateDebut,
            h.dateFin,
            h.etatAdministratifEtablissement  AS etat,
            h.activitePrincipaleEtablissement AS code_ape,
            s.code_commune,
            s.libelle_commune,
            s.code_tranche
        FROM read_parquet('{url_hist}') h
        JOIN (
            SELECT
                siret,
                codeCommuneEtablissement      AS code_commune,
                libelleCommuneEtablissement   AS libelle_commune,
                trancheEffectifsEtablissement AS code_tranche
            FROM read_parquet('{url_stock}')
            WHERE codeCommuneEtablissement = '{COMMUNE}'
              AND statutDiffusionEtablissement = 'O'
        ) s ON h.siret = s.siret
    )
    TO 'data/periodes_sample.parquet' (FORMAT parquet)
""")

n = con.sql("SELECT COUNT(*) FROM 'data/periodes_sample.parquet'").fetchone()[0]
print(f"Échantillon créé : {n} lignes dans data/periodes_sample.parquet")