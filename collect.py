
def collect(con, url_StockEtablissement, url_Historique, departement):
     con.execute("INSTALL httpfs; LOAD httpfs;")
     resultat1=con.sql(f"""
    SELECT siret, 
           codeCommuneEtablissement as code_commune,
                    trancheEffectifsEtablissement as tranche_effectifs,
                    libelleCommuneEtablissement as libelle_commune,
                    activitePrincipaleEtablissement as code_ape
             FROM read_parquet('{url_StockEtablissement}')
                      WHERE substr(codeCommuneEtablissement, 1, 2) = '{departement}'   
                      AND statutDiffusionEtablissement = 'O'
                        
        """)
     
     resultat2=con.sql(f"""
         SELECT ss.siret,
         CAST(ss.dateDebut AS VARCHAR) AS dateDebut,
         CAST(ss.dateFin AS VARCHAR) AS dateFin,
          ss.etatAdministratifEtablissement    AS etat,
            ss.activitePrincipaleEtablissement as code_ape,
          ss.nomenclatureActivitePrincipaleEtablissement as nomenclature_ape
          FROM read_parquet('{url_Historique}') ss
          
         WHERE ss.siret IN (SELECT siret FROM resultat1)
         
     """) 
     return (resultat1, resultat2)

def collect_alt(con, url_StockEtablissement, url_Historique, departement):
  # elle retourne une seule table
  duckDBcursor = con.execute(f"""
                      SELECT
                        s.siret,
                        s.codeCommuneEtablissement AS code_commune,
                        s.trancheEffectifsEtablissement AS tranche_effectifs,
                        s.libelleCommuneEtablissement AS libelle_commune,
                        h.dateDebut,
                        h.dateFin,
                        h.etatAdministratifEtablissement AS etat,
                        h.activitePrincipaleEtablissement AS code_ape,
                        h.nomenclatureActivitePrincipaleEtablissement AS nomenclature_ape
                    FROM read_parquet('{url_StockEtablissement}') AS s
                    LEFT JOIN read_parquet('{url_Historique}') AS h
                        ON s.siret = h.siret
                    WHERE substr(s.codeCommuneEtablissement, 1, 2) = '{departement}' 
                        AND s.statutDiffusionEtablissement = 'O'
                    ORDER BY s.siret, h.dateDebut;
                """)
  return duckDBcursor