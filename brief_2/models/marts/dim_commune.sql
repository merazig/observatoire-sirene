select code_commune, any_value(libelle_commune) as libelle_commune
from {{ ref('stg_periodes') }}
group by code_commune