{% snapshot snap_etat %}
{{ config(unique_key='siret', strategy='check', check_cols=['etat', 'code_ape']) }}
select siret, etat, code_ape from {{ ref('etats_demo') }}
{% endsnapshot %}