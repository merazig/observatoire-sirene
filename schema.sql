CREATE TABLE IF NOT EXISTS dim_commune (
    code_commune VARCHAR(5) PRIMARY KEY,
    libelle_commune TEXT NOT NULL,
    code_departement TEXT NOT NULL,
);

CREATE TABLE IF NOT EXISTS dim_activite(
    code_ape TEXT PRIMARY KEY,
    nomenclature TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_date(
    date_id DATE PRIMARY KEY,
    annee INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    mois INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_tranche_effectifs(
    code_tranche TEXT PRIMARY KEY,
    libelle TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS fait_etablissement_version (
    siret         TEXT        NOT NULL,
    valid_from    DATE        NOT NULL REFERENCES dim_date(date_id),
    valid_to      DATE,
    is_current    BOOLEAN     NOT NULL,
    code_commune  TEXT        REFERENCES dim_commune(code_commune),
    code_ape      TEXT        REFERENCES dim_activite(code_ape),
    code_tranche  TEXT        REFERENCES dim_tranche_effectifs(code_tranche),
    etat          TEXT        NOT NULL, PRIMARY KEY (siret, valid_from)
);