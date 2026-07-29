
---

# Livrable 2 : `DECISIONS.md`

```markdown
# Décisions d'architecture et d'implémentation

## 1. Périmètre
- **Paramètre** : `DEPARTEMENTS = ['69']` (liste Python).
- Aucun `'69'` en dur dans le code SQL.
- Le même code fonctionnera pour `['01','03',...]` (ARA) ou `None` (France).

## 2. RGPD
- **Règle** : `statutDiffusionEtablissement = 'O'` appliqué **en amont** (acquisition).
- **Attributs exclus** : toute colonne contenant un nom personnel (`denominationUsuelle`, `nom`, `prenom`, etc.) est ignorée.
- Le fait ne contient **pas** de dénomination.

## 3. Colonnes suivies dans le SCD2
Le brief impose que seuls `(code_ape, etat)` déclenchent une nouvelle version.
- `code_commune` et `code_tranche` viennent du **stock** (non historisés dans SIRENE).
- `code_ape` et `etat` viennent de l'**historique** (historisés).
- La dénomination n'est **pas** suivie.

## 4. Gestion des dates aberrantes
- **Fourchette prise en consideration** : `['1900-01-01', '2026-O7-31']`.(current_date)
- Les périodes hors fourchette sont **conservées dans l'entrepôt** mais **exclues des analyses temporelles**.
- Justification : éviter les dates comme l'an 1 ou 7490 qui corrompent les agrégations par an.

## 5. Technologie
- **Acquisition** : DuckDB (lecture Parquet distant via httpfs, écriture Parquet local).
- **Transformation** : DuckDB (SQL) pour tenir le volume France du brief 2.
- **Analyses** : DuckDB SQL + pandas pour les petits résultats et graphes.
- **Pas de PostgreSQL** pour le stockage intermédiaire (inutile sur Rhône, limitant pour la France).

## 6. Pipeline(modifiableen fonction des .py que l'on decide de crées)
-
-
-
-
## 7. Stratégie SCD2
- Tri par `siret, dateDebut`.
- `LAG(code_ape, etat)` pour détecter le changement.(pas sur de prendre cette option on reflechie a plus simple)
- Regroupement des périodes consécutives de même `(code_ape, etat)`.
- `valid_from` = `dateDebut` de la première période du groupe.
- `valid_to` = `dateFin` de la dernière période du groupe (null si courant).
- `is_current` = True si `valid_to IS NULL`.

## 8. Git / Déploiement
- `.gitignore` : `data/`, `*.parquet`, `__pycache__/`, `.env`.
- Pas de secret versionné.
- `main` toujours exécutable : les scripts vérifient l'existence des fichiers intermédiaires.