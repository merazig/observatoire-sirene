
  
  create view "entrepot"."main"."stg_periodes__dbt_tmp" as (
    select siret, dateDebut as date_debut, dateFin as date_fin,
       etat, code_ape, code_commune, libelle_commune, code_tranche
from 'data/periodes_sample.parquet'
  );
