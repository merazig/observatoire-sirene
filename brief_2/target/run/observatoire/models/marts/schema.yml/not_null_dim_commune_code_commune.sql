
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select code_commune
from "entrepot"."main"."dim_commune"
where code_commune is null



  
  
      
    ) dbt_internal_test