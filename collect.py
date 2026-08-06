
def collect(con, url_StockEtablissement, url_Historique, departement):
     con.execute("INSTALL httpfs; LOAD httpfs;")
     resultat1=con.sql(f"""
    SELECT siret, 
           codeCommuneEtablissement as code_commune,
                    trancheEffectifsEtablissement as tranche_effectifs,
                    libelleCommuneEtablissement as libelle_commune
             FROM read_parquet('{url_StockEtablissement}')
                      WHERE substr(codeCommuneEtablissement, 1, 2) = '{departement}'   
                      AND statutDiffusionEtablissement = 'O'
                        
        """)
     
     resultat2=con.sql(f"""
         SELECT ss.siret,
         CAST(ss.dateDebut AS VARCHAR) AS dateDebut,
          ss.etatAdministratifEtablissement    AS etat,
            ss.activitePrincipaleEtablissement as code_ape,
          ss.nomenclatureActivitePrincipaleEtablissement as nomenclature_ape
          FROM read_parquet('{url_Historique}') ss
          
         WHERE ss.siret IN (SELECT siret FROM resultat1)
         
     """) 
     return (resultat1, resultat2)

def collect_alt(con, url_StockEtablissement, url_Historique, departement):
  # elle retourne une seule table
  duckDBcursor = con.sql(f"""
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

def collect_alt2(con, url_StockEtablissement, url_Historique, departement):
  # elle retourne une seule table
  duckDBcursor = con.sql(f"""
                        WITH etab AS (
                            SELECT
                                siret,
                                codeCommuneEtablissement,
                                trancheEffectifsEtablissement,
                                libelleCommuneEtablissement
                            FROM read_parquet('{url_StockEtablissement}')
                            WHERE codeCommuneEtablissement LIKE '{departement}%'
                            AND statutDiffusionEtablissement = 'O'
                        )

                        SELECT
                            e.siret,
                            e.codeCommuneEtablissement AS code_commune,
                            e.trancheEffectifsEtablissement AS tranche_effectifs,
                            e.libelleCommuneEtablissement AS libelle_commune,
                            h.dateDebut,
                            h.dateFin,
                            h.etatAdministratifEtablissement,
                            h.activitePrincipaleEtablissement,
                            h.nomenclatureActivitePrincipaleEtablissement
                        FROM etab e
                        LEFT JOIN read_parquet('{url_Historique}') h
                        ON e.siret = h.siret
                        ORDER BY e.siret, h.dateDebut;
                """)
  return duckDBcursor