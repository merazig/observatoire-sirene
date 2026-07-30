
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    code_commune as unique_field,
    count(*) as n_records

from "entrepot"."main"."dim_commune"
where code_commune is not null
group by code_commune
having count(*) > 1



  
  
      
    ) dbt_internal_test