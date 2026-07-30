
  
  create view "entrepot"."main"."dim_commune__dbt_tmp" as (
    select code_commune, any_value(libelle_commune) as libelle_commune
from "entrepot"."main"."stg_periodes"
group by code_commune
  );
