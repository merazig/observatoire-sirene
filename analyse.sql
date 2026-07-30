-- ============================================================
-- analyse.sql — Observatoire du tissu économique (Rhône)
-- Livrable complet : analyses métier + qualité des données + gouvernance/RGPD
--
-- A. Analyses métier       (état courant / historique / dynamique)
-- B. Qualité des données   (NULL, doublons, cohérence, FK, dates)
-- C. Gouvernance / RGPD    (inventaire, minimisation, traçabilité, conservation)
--
-- Fourchette de dates plausibles : 2015-2026 (cf DECISIONS.md)
-- ============================================================


-- ============================================================
-- A. ANALYSES MÉTIER
-- ============================================================

-- ------------------------------------------------------------
-- A.1 État courant
-- ------------------------------------------------------------

-- A.1.1 Nombre d'établissements actifs aujourd'hui (attendu ≈ 430 000)
SELECT count(*) AS nb_actifs
FROM fait_etablissement_version
WHERE is_current AND etat = 'A';

-- A.1.2 Top 10 secteurs (code NAF) parmi les actifs
-- (attendu : top 1 location immobilière, 68.20B / 68.20A)
SELECT
    f.code_ape,
    count(*) AS nb_etablissements
FROM fait_etablissement_version f
WHERE f.is_current AND f.etat = 'A'
GROUP BY f.code_ape
ORDER BY nb_etablissements DESC
LIMIT 10;

-- A.1.3 Top communes par nombre d'établissements actifs
-- (attendu : Lyon, Villeurbanne, Vénissieux, Saint-Priest)
SELECT
    d.libelle_commune,
    count(*) AS nb_etablissements
FROM fait_etablissement_version f
JOIN dim_commune d ON f.code_commune = d.code_commune
WHERE f.is_current AND f.etat = 'A'
GROUP BY d.libelle_commune
ORDER BY nb_etablissements DESC
LIMIT 10;

-- A.1.4 Répartition des établissements actifs par tranche d'effectifs
-- (attention : beaucoup de NN, non renseigné)
SELECT
    f.code_tranche,
    t.libelle,
    count(*) AS nb_etablissements
FROM fait_etablissement_version f
JOIN dim_tranche_effectifs t ON f.code_tranche = t.code_tranche
WHERE f.is_current AND f.etat = 'A'
GROUP BY f.code_tranche, t.libelle
ORDER BY f.code_tranche;

-- A.1.5 BONUS — estimation du nombre d'emplois dans les établissements actifs
-- Hypothèse forte : milieu de fourchette par tranche (NN exclu). Ordre de
-- grandeur uniquement, jamais présenté comme un chiffre officiel.
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

-- ------------------------------------------------------------
-- A.2 Évolution historique
-- ------------------------------------------------------------

-- A.2.1 Établissements actifs au 1er janvier 2020
SELECT count(*) AS nb_actifs_2020
FROM fait_etablissement_version
WHERE etat = 'A'
  AND valid_from <= DATE '2020-01-01'
  AND (valid_to IS NULL OR valid_to > DATE '2020-01-01');

-- A.2.2 Évolution des secteurs entre le 01/01/2020 et aujourd'hui
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
-- tri DESC = secteurs qui progressent le plus en tête ; ASC = qui reculent le plus

-- A.2.3 Historique d'un établissement (activité à une date passée)
-- Remplacer '<SIRET_A_CHOISIR>' par un siret ayant changé d'APE. Pour en trouver un :
--   SELECT siret FROM fait_etablissement_version GROUP BY siret HAVING count(*) > 1 LIMIT 1;
SELECT siret, valid_from, valid_to, is_current, code_ape, etat
FROM fait_etablissement_version
WHERE siret = '<SIRET_A_CHOISIR>'
ORDER BY valid_from;

-- ------------------------------------------------------------
-- A.3 Dynamique
-- ------------------------------------------------------------

-- A.3.1 Créations par an (première version de chaque établissement)
-- Piège qualité : filtrer sur 2015-2026 (dates corrompues an 1 à an 7490, cf DECISIONS.md)
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

-- A.3.2 Fermetures par an (transitions A -> F)
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

-- A.3.3 Solde net (créations - fermetures) par an et par secteur
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


-- ============================================================
-- B. QUALITÉ DES DONNÉES
-- ============================================================

-- B.1 Nombre de SIRET distincts
SELECT count(DISTINCT siret) AS nb_siret_distincts
FROM fait_etablissement_version;

-- B.2 Valeurs NULL par colonne
SELECT
    count(*) AS total,
    count(*) - count(code_commune) AS null_code_commune,
    count(*) - count(code_ape) AS null_code_ape,
    count(*) - count(code_tranche) AS null_code_tranche,
    count(*) - count(valid_to) AS null_valid_to  -- normal pour is_current = TRUE
FROM fait_etablissement_version;

-- B.3 Répartition des états (A, F, ...)
SELECT etat, count(*) AS nb_versions
FROM fait_etablissement_version
GROUP BY etat
ORDER BY nb_versions DESC;

-- B.4 Doublons de clé primaire (siret, valid_from)
-- Doit retourner 0 ligne : la PK l'interdit déjà, ceci en est la preuve documentée
SELECT siret, valid_from, count(*)
FROM fait_etablissement_version
GROUP BY siret, valid_from
HAVING count(*) > 1;

-- B.5 Intégrité des clés étrangères — communes inexistantes
SELECT f.*
FROM fait_etablissement_version f
LEFT JOIN dim_commune c ON f.code_commune = c.code_commune
WHERE f.code_commune IS NOT NULL AND c.code_commune IS NULL;

-- B.6 Intégrité des clés étrangères — codes APE inconnus
SELECT f.*
FROM fait_etablissement_version f
LEFT JOIN dim_activite a ON f.code_ape = a.code_ape
WHERE f.code_ape IS NOT NULL AND a.code_ape IS NULL;

-- B.7 Intégrité des clés étrangères — tranches d'effectifs inconnues
SELECT f.*
FROM fait_etablissement_version f
LEFT JOIN dim_tranche_effectifs t ON f.code_tranche = t.code_tranche
WHERE f.code_tranche IS NOT NULL AND t.code_tranche IS NULL;

-- B.8 Une seule version courante par SIRET
-- Doit retourner 0 ligne
SELECT siret, count(*) AS nb_versions_courantes
FROM fait_etablissement_version
WHERE is_current
GROUP BY siret
HAVING count(*) > 1;

-- B.9 Cohérence valid_from < valid_to
-- Doit retourner 0 ligne
SELECT *
FROM fait_etablissement_version
WHERE valid_to IS NOT NULL AND valid_to <= valid_from;

-- B.10 Dates hors plage plausible (2015-2026)
-- Révèle les dates corrompues de la source SIRENE (an 1 à an 7490)
SELECT *
FROM fait_etablissement_version
WHERE EXTRACT(YEAR FROM valid_from) NOT BETWEEN 2015 AND 2026
   OR (valid_to IS NOT NULL AND EXTRACT(YEAR FROM valid_to) NOT BETWEEN 2015 AND 2026);


-- ============================================================
-- C. GOUVERNANCE / RGPD
-- ============================================================
-- Ce ne sont plus des statistiques métier, mais des contrôles de
-- gouvernance inspirés des principes RGPD (minimisation, traçabilité,
-- conservation). Ce n'est pas un audit RGPD complet : voir AUDIT_RGPD.md
-- pour le cadrage détaillé (base légale, cas des auto-entrepreneurs, etc.)

-- C.1 Inventaire des données stockées
SELECT *
FROM fait_etablissement_version
LIMIT 20;

-- C.2 Vérification de l'absence de données personnelles directes
-- (pas de requête : contrôle documentaire — colonnes du schéma = siret, code_ape,
-- code_commune, code_tranche, etat, valid_from, valid_to, is_current. Aucun nom,
-- adresse précise, contact. Voir AUDIT_RGPD.md §1 pour la nuance sur les EI.)

-- C.3 Principe de minimisation — le modèle ne conserve que les colonnes utiles
SELECT
    siret,
    code_commune,
    code_ape,
    code_tranche,
    etat
FROM fait_etablissement_version
LIMIT 20;

-- C.4 Intégrité référentielle (synthèse gouvernance des contrôles B.5/B.6/B.7)
SELECT
    (SELECT count(*) FROM fait_etablissement_version f
        LEFT JOIN dim_commune c ON f.code_commune = c.code_commune
        WHERE f.code_commune IS NOT NULL AND c.code_commune IS NULL) AS communes_orphelines,
    (SELECT count(*) FROM fait_etablissement_version f
        LEFT JOIN dim_activite a ON f.code_ape = a.code_ape
        WHERE f.code_ape IS NOT NULL AND a.code_ape IS NULL) AS activites_orphelines,
    (SELECT count(*) FROM fait_etablissement_version f
        LEFT JOIN dim_tranche_effectifs t ON f.code_tranche = t.code_tranche
        WHERE f.code_tranche IS NOT NULL AND t.code_tranche IS NULL) AS tranches_orphelines;

-- C.5 Historisation des données (traçabilité) — versions non courantes conservées
SELECT *
FROM fait_etablissement_version
WHERE is_current = FALSE
LIMIT 100;

-- C.6 Durée de conservation par version
SELECT
    siret,
    valid_from,
    valid_to,
    valid_to - valid_from AS duree_jours
FROM fait_etablissement_version
WHERE valid_to IS NOT NULL
ORDER BY duree_jours DESC;

-- C.7 Cohérence des versions (une version courante par siret, synthèse gouvernance)
SELECT siret, count(*) AS nb_versions_courantes
FROM fait_etablissement_version
WHERE is_current
GROUP BY siret
HAVING count(*) > 1;
-- doit retourner 0 ligne

-- C.8 Complétude des données (synthèse gouvernance du contrôle B.2)
SELECT
    round(100.0 * count(code_commune) / count(*), 2) AS pct_commune_renseignee,
    round(100.0 * count(code_ape) / count(*), 2) AS pct_ape_renseignee,
    round(100.0 * count(code_tranche) / count(*), 2) AS pct_tranche_renseignee
FROM fait_etablissement_version;
