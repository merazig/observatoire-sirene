# Décisions d'architecture et d'implémentation

## 1. Périmètre

- Paramètre `DEPT` : code département, passé en argument de ligne de commande (`sys.argv[1]`, valeur par défaut `'69'`), aucune valeur en dur ailleurs dans le code.
- Limite actuelle : le pipeline traite un seul département par exécution (filtre par égalité). Le passage à la région ARA nécessitera soit plusieurs exécutions successives, soit une évolution du filtre vers une liste de codes.

## 2. RGPD

### 2.1 Filtre de diffusion

- Seuls les établissements avec `statutDiffusionEtablissement = 'O'` sont retenus. Le filtre est posé dès l'acquisition (`collect.py`), sur le stock ; l'historique hérite du filtre par jointure sur `siret`.
- Alternative écartée : masquage colonne par colonne des établissements en `'P'` (diffusion partielle). Choix retenu : exclusion totale — plus simple à implémenter et plus sûre (pas de risque de fuite résiduelle via une colonne mal évaluée), au prix d'une sous-couverture du territoire : les établissements en opposition sont absents de l'observatoire. Cette limite est documentée, pas un défaut caché — les comptages par commune/secteur sont un plancher, pas un total exhaustif.

### 2.2 Attributs de personne physique

- Aucune colonne de nom ou d'enseigne n'entre dans l'entrepôt, y compris pour les établissements en `'O'` — imposé à la fois par le RGPD et par le contrat de données du PM (le fait ne porte pas d'attribut de dénomination).
- Le représentant légal (personne morale) n'est jamais diffusé en Open Data quel que soit le statut de diffusion (art. R 123-232 du Code de commerce) : contrainte de la source, pas un choix de conception.

### 2.3 Article 22 — profilage et décision automatisée

- Le traitement est hors du champ d'application de l'article 22 : l'observatoire ne produit que des agrégats statistiques (comptages par commune, secteur, année) et ne fonde aucune décision individualisée. Aucune mesure de conformité spécifique n'est donc mise en œuvre à ce titre.

## 3. Modèle de données

**Fait** — `fait_etablissement_version` (SCD2), clé primaire `(siret, valid_from)` :
`siret, valid_from, valid_to, is_current, code_commune, code_ape, code_tranche, etat`.

- `code_ape` et `etat` sont les seules colonnes qui déclenchent l'ouverture d'une nouvelle version.
- `code_commune` et `code_tranche` proviennent du stock (valeur actuelle), appliqués à toutes les versions d'un siret — l'historique SIRENE ne les porte pas dans le temps.
- La dénomination et l'enseigne ne sont jamais suivies (cf. exemple THE ONLY PLACE du brief : un changement de nom seul ne crée pas de version).

**Dimensions** :
- `dim_activite` (`code_ape`, `nomenclature`) — valeurs distinctes de l'historique.
- `dim_tranche_effectifs` (`code_tranche`, `libelle`) — référentiel INSEE des 16 tranches, codé en dur.
- `dim_commune` (`code_commune`, `libelle_commune`, `code_departement`) — depuis le stock, `code_departement` dérivé de `code_commune`.
- `dim_date` (`date_id`, `annee`, `trimestre`, `mois`) — dates de début de période observées dans l'historique.

**Contraintes** : clés étrangères nullables du fait vers `dim_commune`, `dim_activite`, `dim_tranche_effectifs` ; `valid_from` est `NOT NULL` et référence `dim_date`.

## 4. Gestion des dates aberrantes

- **Décision** : conserver les dates brutes dans l'entrepôt et ne filtrer qu'au niveau des analyses, sur la fourchette 2015–2026, plutôt que de corriger ou d'exclure la donnée source.
- **Justification** : l'historique SIRENE contient des dates allant de l'an 1 à l'an 7490 (erreurs de saisie/migration côté INSEE). Corriger la donnée source est hors périmètre du projet ; on documente le filtre au niveau de l'usage plutôt que de le cacher en réécrivant la donnée brute.
- Un outil de diagnostic (`check_dates_aberrantes`) calcule les bornes et les compteurs d'anomalies (dates hors plage, incohérences `dateFin`/`dateDebut`) sur l'historique brut, à des fins de contrôle qualité.

## 5. Choix techniques

- **Acquisition** (`collect.py`) : DuckDB + `httpfs` en lecture distante sur les Parquet SIRENE, sans téléchargement complet. Sortie en deux relations distinctes (stock, historique), non jointes, pour permettre le regroupement SCD2 en aval sans jointure prématurée.
- **Transformation** (`clean.py`) : pandas — tri, détection des changements de version, regroupement des périodes consécutives.
- **Chargement** (`load.py`) : PostgreSQL, via `psycopg2`/`execute_values`, avec idempotence (`ON CONFLICT DO NOTHING` sur les clés primaires du schéma).
- **Analyses** (`analyse.sql`) : SQL exécuté directement sur PostgreSQL.

## 6. Pipeline

1. `collect.py` — lecture distante SIRENE, filtre RGPD et filtre périmètre appliqués au stock, historique restreint aux `siret` retenus.
2. `clean.py` — construction du fait SCD2 (§7) et des dimensions `dim_activite` / `dim_tranche_effectifs`.
3. `load.py` — chargement des dimensions puis du fait dans PostgreSQL, connexion via variables d'environnement (`.env`).
4. `main.py` — orchestration : création du schéma, exécution séquentielle des étapes ci-dessus, validation de la transaction.
5. `analyse.sql` — requêtes métier : état courant (actifs, top secteurs, top communes, répartition par tranche, emplois estimés), état à une date passée, dynamique (créations/fermetures/solde par an et par secteur).

## 7. Stratégie SCD2

- Tri par `siret, dateDebut`.
- Détection de changement par comparaison d'une clé concaténée `code_ape|etat` avec celle de la ligne précédente du même siret.
- Une nouvelle version s'ouvre à chaque changement de clé ; les périodes consécutives partageant la même clé sont regroupées.
- `is_current = True` pour la dernière version de chaque siret (`valid_to` non renseigné).

## 8. Git / Déploiement

- `.gitignore` : `data/`, `*.parquet`, `__pycache__/`, `.env`.
- Aucun secret versionné ; connexion à PostgreSQL via variables d'environnement (`python-dotenv`).
- Le pipeline vérifie l'existence de ses fichiers intermédiaires avant exécution.

## 9. Limites connues et points à corriger

- Le filtre de dates est actuellement appliqué à la fois dans `clean.py` (au niveau des lignes du fait) et dans `analyse.sql` (au niveau des agrégats), avec deux fourchettes différentes. À unifier : ne filtrer qu'au niveau des analyses, conformément à la décision du §4.
- Le filtre sur `dateFin` dans `clean.py` exclut les lignes sans `dateFin` (établissements encore actifs), faute d'autoriser explicitement les valeurs nulles. À corriger en priorité — risque de perte des établissements actuellement actifs.
- La colonne `valid_to` exportée reflète la date de fin de la première période du groupe, et non la véritable fin de version. À corriger avant mise en production.
- Le pipeline ne traite qu'un département par exécution (§1), alors que le passage à l'échelle ARA/France est prévu au brief suivant.
- `collect_alt()` (jointure stock/historique anticipée) est du code mort, non utilisé par le pipeline — à retirer.
- PostgreSQL est utilisé comme stockage final ; ce choix mériterait d'être justifié explicitement dans la documentation (accès concurrent, outillage d'analyse standard, etc.).
- `check_dates_aberrantes` n'est pas encore intégré à `main.py`.

## 10. Industrialisation avec dbt (en cours)

- **Décision** : l'entrepôt manuel (Python/DuckDB/PostgreSQL, décrit ci-dessus) est reconstruit avec dbt. `dbt run` a montré un gain net en rapidité d'exécution et en facilité d'usage par rapport au pipeline manuel.
- **Matérialisation** : `{{ config(materialized='table') }}` en tête d'un modèle indique à dbt de matérialiser le résultat en table physique dans l'entrepôt, plutôt qu'en vue.
  - Table : donnée persistée physiquement — lecture plus rapide pour les modèles interrogés fréquemment ou en aval d'autres modèles, au prix d'un espace de stockage et d'un temps de rebuild à chaque `dbt run`.
  - Vue : requête recalculée à chaque lecture, sans stockage — adaptée aux modèles légers ou peu sollicités (typiquement le staging).
- **Constat mesuré** : matérialiser en `view` plutôt qu'en `table` divise le temps par deux. C'est un argument concret en faveur des vues pour les modèles qui n'ont pas besoin d'être persistés (staging, modèles intermédiaires peu réutilisés) — à confirmer si ce gain a été mesuré sur le temps de `dbt run`, sur le chargement vers PostgreSQL, ou sur les deux, pour savoir sur quels modèles précisément l'appliquer.
- **Constat** : `dbt run` est rapide sur la partie transformation, mais un ralentissement net est observé au moment de charger le résultat vers PostgreSQL — contraste à noter avec le gain de rapidité mis en avant plus haut, qui ne concerne donc que l'étape de transformation, pas le chargement final.
- **Architecture du projet dbt** (d'après ta description, détail des modèles à confirmer avec les fichiers) :
  - `data/` — fichiers Parquet en sortie de dbt.
  - `staging/` — modèles de nettoyage/préparation, distincts par source.
  - Modèles de fait et de dimensions (`dim_*`), dont une **dimension département** qui alimente les autres dimensions (probablement le référentiel géographique partagé entre `dim_commune` et les futurs départements ARA — à confirmer si elle répond au point ouvert du §1 sur le passage à plusieurs départements).
  - `snapshot/` — gère l'historisation (SCD2) via `dbt snapshot`, en remplacement de la logique manuelle `clean.py`/§7.
  - `profiles.yml` — configuration de connexion dbt.
- **Chargement vers PostgreSQL** : un script séparé, `data-postgres.py`, lit les Parquet produits par dbt et les charge vers PostgreSQL — c'est cette étape, externe à dbt, qui est concernée par le ralentissement constaté plus haut (dbt lui-même reste rapide sur la partie transformation). Mécanisme de chargement (par lot ou ligne à ligne) à vérifier une fois le contenu de `data-postgres.py` partagé, avant de conclure si c'est à optimiser ou une limite acceptée.
- *(section à compléter avec le schéma dbt complet — modèles staging/marts, découpage table/vue par modèle, et `dbt snapshot` pour la partie SCD2.)*