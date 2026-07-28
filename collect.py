import duckdb
import pandas as pd 


def collect(con, url_StockEtablissement, url_Historique, departement):
     con.execute("INSTALL httpfs; LOAD httpfs;")
     resultat1=con.sql(f"""
    SELECT siret, 
           codeCommuneEtablissement as code_commune,
                    trancheEffectifsEtablissement as tranche_effectifs,
                    dateCreationEtablissement,
                    libelleCommuneEtablissement as libelle_commune,
                    activitePrincipaleEtablissement as code_ape,
                    nomenclatureActivitePrincipaleEtablissement as nomenclature_ape
             FROM read_parquet('{url_StockEtablissement}')
                      WHERE substr(codeCommuneEtablissement, 1, 2) = '{departement}'   
                      AND statutDiffusionEtablissement = 'O'              
        """)
     
     resultat2=con.sql(f"""
         SELECT ss.siret,ss.dateFin,ss.dateDebut , ss.etatAdministratifEtablissement    AS etat, ss.activitePrincipaleEtablissement  
          FROM read_parquet('{url_Historique}') ss
          
         WHERE ss.siret IN (SELECT siret FROM resultat1)
      
""") 
     return (resultat1, resultat2)







