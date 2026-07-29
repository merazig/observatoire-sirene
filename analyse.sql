-- Analyses métier — Observatoire du tissu économique (Rhône)

-- ÉTAT COURANT


-- Établissements actifs aujourd'hui 
SELECT count(*) AS nb_actifs
FROM fait_etablissement_version
WHERE is_current AND etat = 'A';


-- Top 10 secteurs (code NAF)
SELECT
    f.code_ape,
    count(*) AS nb_etablissements
FROM fait_etablissement_version f
WHERE f.is_current AND f.etat = 'A'
GROUP BY f.code_ape
ORDER BY nb_etablissements DESC
LIMIT 10;


--Top communes par nombre d'établissements actifs

SELECT
    d.libelle_commune,
    count(*) AS nb_etablissements
FROM fait_etablissement_version f
JOIN dim_commune d ON f.code_commune = d.code_commune
WHERE f.is_current AND f.etat = 'A'
GROUP BY d.libelle_commune
ORDER BY nb_etablissements DESC
LIMIT 10;


--Répartition des établissements actifs par tranche d'effectifs

SELECT
    f.code_tranche,
    t.libelle,
    count(*) AS nb_etablissements
FROM fait_etablissement_version f
JOIN dim_tranche_effectifs t ON f.code_tranche = t.code_tranche
WHERE f.is_current AND f.etat = 'A'
GROUP BY f.code_tranche, t.libelle
ORDER BY f.code_tranche;


-- Estimation du nombre d'emplois dans les établissements actifs

SELECT
    sum(
        CASE f.code_tranche
            WHEN '00' THEN 0
            WHEN '01' THEN 1.5
            WHEN '02' THEN 4
            WHEN '03' THEN 7.5
            WHEN '11' THEN 15
            WHEN '12' THEN 35
            WHEN '21' THEN 75
            WHEN '22' THEN 150
            WHEN '31' THEN 225
            WHEN '32' THEN 375
            WHEN '41' THEN 750
            WHEN '42' THEN 1500
            WHEN '51' THEN 3500
            WHEN '52' THEN 7500
            WHEN '53' THEN 12000
            ELSE 0  -- NN exclu de l'estimation
        END
    ) AS emplois_estimes
FROM fait_etablissement_version f
WHERE f.is_current AND f.etat = 'A';


--UNE DATE PASSÉE (exemple : 1er janvier 2020)

-- Établissements actifs au 1er janvier 2020
SELECT count(*) AS nb_actifs_2020
FROM fait_etablissement_version
WHERE etat = 'A'
  AND valid_from <= DATE '2020-01-01'
  AND (valid_to IS NULL OR valid_to > DATE '2020-01-01');


-- Secteurs qui ont progressé ou  reculé entre le 01/01/2020 à aujourd'hui
WITH avant AS (
    SELECT code_ape, count(*) AS nb_avant
    FROM fait_etablissement_version
    WHERE etat = 'A'
      AND valid_from <= DATE '2020-01-01'
      AND (valid_to IS NULL OR valid_to > DATE '2020-01-01')
    GROUP BY code_ape
),
apres AS (
    SELECT code_ape, count(*) AS nb_apres
    FROM fait_etablissement_version
    WHERE is_current AND etat = 'A'
    GROUP BY code_ape
)
SELECT
    COALESCE(a.code_ape, b.code_ape) AS code_ape,
    COALESCE(nb_avant, 0) AS nb_avant,
    COALESCE(nb_apres, 0) AS nb_apres,
    COALESCE(nb_apres, 0) - COALESCE(nb_avant, 0) AS variation
FROM avant a
FULL OUTER JOIN apres b USING (code_ape)
ORDER BY variation DESC;



-- Activité d'un établissement à une date passée

SELECT siret, valid_from, valid_to, is_current, code_ape, etat
FROM fait_etablissement_version
WHERE siret = '<SIRET_A_CHOISIR>'   -- Remplacer '<SIRET_A_CHOISIR>' par un siret ayant changé d'APE.
ORDER BY valid_from;



--LA DYNAMIQUE (créations, fermetures, solde)


--Créations par an (première version de chaque établissement)
-- Piège qualité : filtrer sur 2015-2026, sinon des années aberrantes apparaissent

WITH premieres AS (
    SELECT siret, MIN(valid_from) AS date_creation
    FROM fait_etablissement_version
    GROUP BY siret
)
SELECT
    EXTRACT(YEAR FROM date_creation)::INTEGER AS annee,
    count(*) AS nb_creations
FROM premieres
WHERE EXTRACT(YEAR FROM date_creation) BETWEEN 2015 AND 2026
GROUP BY annee
ORDER BY annee;


--Fermetures par an (transitions A -> F)
WITH ordonne AS (
    SELECT
        siret,
        valid_from,
        etat,
        LAG(etat) OVER (PARTITION BY siret ORDER BY valid_from) AS etat_precedent
    FROM fait_etablissement_version
)
SELECT
    EXTRACT(YEAR FROM valid_from)::INTEGER AS annee,
    count(*) AS nb_fermetures
FROM ordonne
WHERE etat = 'F'
  AND etat_precedent = 'A'
  AND EXTRACT(YEAR FROM valid_from) BETWEEN 2015 AND 2026
GROUP BY annee
ORDER BY annee;


--Solde net (créations - fermetures) par an et par secteur
WITH premieres AS (
    SELECT siret, code_ape, MIN(valid_from) AS date_creation
    FROM fait_etablissement_version
    GROUP BY siret, code_ape
),
ordonne AS (
    SELECT
        siret,
        code_ape,
        valid_from,
        etat,
        LAG(etat) OVER (PARTITION BY siret ORDER BY valid_from) AS etat_precedent
    FROM fait_etablissement_version
),
creations AS (
    SELECT
        code_ape,
        EXTRACT(YEAR FROM date_creation)::INTEGER AS annee,
        count(*) AS nb_creations
    FROM premieres
    WHERE EXTRACT(YEAR FROM date_creation) BETWEEN 2015 AND 2026
    GROUP BY code_ape, annee
),
fermetures AS (
    SELECT
        code_ape,
        EXTRACT(YEAR FROM valid_from)::INTEGER AS annee,
        count(*) AS nb_fermetures
    FROM ordonne
    WHERE etat = 'F'
      AND etat_precedent = 'A'
      AND EXTRACT(YEAR FROM valid_from) BETWEEN 2015 AND 2026
    GROUP BY code_ape, annee
)
SELECT
    COALESCE(c.code_ape, f.code_ape) AS code_ape,
    COALESCE(c.annee, f.annee) AS annee,
    COALESCE(c.nb_creations, 0) AS creations,
    COALESCE(f.nb_fermetures, 0) AS fermetures,
    COALESCE(c.nb_creations, 0) - COALESCE(f.nb_fermetures, 0) AS solde
FROM creations c
FULL OUTER JOIN fermetures f USING (code_ape, annee)
ORDER BY annee, solde DESC;
