# Note de faisabilité — Observatoire du tissu économique (Rhône)

## 1. Cartographie des données

### StockEtablissement (~2,2 Go, 43,7 M lignes au national)
État courant de chaque établissement — une ligne par siret.

| Colonne | Historisée ? | Usage prévu |
|---|---|---|
| `siret` | non (identifiant) | clé du fait |
| `codeCommuneEtablissement` | non — valeur courante seulement | `dim_commune` |
| `libelleCommuneEtablissement` | non | `dim_commune` |
| `trancheEffectifsEtablissement` | non — valeur courante seulement | `dim_tranche_effectifs` |
| `activitePrincipaleEtablissement` | oui (voir historique) | jointure vers le fait |
| `statutDiffusionEtablissement` | — | filtre RGPD |
| `denominationUsuelleEtablissement` / `enseigne*` | oui | **non suivi** (hors contrat, cf. §4) |


### StockEtablissementHistorique (~0,87 Go, 95,3 M périodes au national)
Une ligne par établissement **et par période de validité** `[dateDebut, dateFin[`.

| Colonne | Historisée ? | Usage prévu |
|---|---|---|
| `siret` | — | clé du fait |
| `dateDebut` / `dateFin` | oui, par définition | `valid_from` / `valid_to` |
| `etatAdministratifEtablissement` (A/F) | oui | attribut du fait |
| `activitePrincipaleEtablissement` | oui | `fait_etablissement_version.code_ape` |
| `nomenclatureActivitePrincipaleEtablissement` | oui | `dim_activite.nomenclature` |
| `denominationUsuelleEtablissement` | oui | **non suivi** (le contrat ignore le nom) |


## 2. Volumétrie

| Périmètre | Établissements diffusibles | Périodes historisées |
|---|---|---|
| Rhône (69) — **mesuré** | **1 202 304** | **2 652 621** |
| Région ARA (12 dépt.) | ordre de grandeur ×6 à ×8 | idem |
| France entière | 43,7 M (stock) | 95,3 M (historique) |

Chiffres du Rhône mesurés via `collect.py` en lecture distante duckdb + httpfs. 
La projection région/France anticipe le passage à l'échelle : au-delà du Rhône, 
`pandas` en mémoire complète atteint ses limites, 
la lecture colonnes de `duckdb` reste nécessaire.

## 3. Qualité des données

- **`NN`** : tranche d'effectifs non renseignée — valeur fréquente à ne pas
  confondre avec une vraie tranche. Elle est conservée dans `dim_tranche_effectifs`
  (libellé « non renseigné ») mais **exclue des agrégats d'emploi** (l'estimation
  d'effectifs lui attribue 0, cf. `analyse.sql`).
- **`[ND]`** : dénomination non diffusée — sans impact ici puisque le contrat ne
  suit pas la dénomination.
- **Dates aberrantes** : mesure réelle sur l'historique du Rhône (2 652 621
  lignes) via `quality.py::check_dates_aberrantes()` :

  | Contrôle | Nb de lignes |
  |---|---|
  | Date de début antérieure à 1900 (jusqu'à l'an 4) | 21 |
  | Date de début dans le futur (jusqu'en 3035) | 70 |
  | Date de fin dans le futur | 11 |
  | Date de fin antérieure au début | 0 |

  Soit environ 102 lignes sur 2,65 M (**~0,004 %**). L'aberration maximale mesurée
  est l'an 3035. 
  Décision retenue : ne pas corriger la donnée source et supprimer les dates aberrantes, 
  et borner les analyses temporelles sur 2015–2026 (cf. `analyse.sql` et `DECISIONS.md`).

## 4. RGPD

`statutDiffusionEtablissement` encode la diffusibilité :
- `'O'` : diffusible
- `'P'` : diffusion restreinte (entrepreneur individuel ayant demandé le masquage — la fiche peut porter un nom de personne physique)

**Règle appliquée** : ne conserver que les `'O'`, filtrées dès la collecte (avant toute autre transformation), 
et ne jamais reprendre de colonne de nom/dénomination dans l'entrepôt final.

## 5. Preuve de faisabilité technique

Chiffre choisi : **nombre d'établissements diffusibles du Rhône**, 
calculé via `duckdb` + `httpfs` en lecture distante sur les Parquet SIRENE (sans téléchargement complet, lecture en colonnes).

```
Établissements (stock, diffusibles) : 1 202 304
Périodes (historique, diffusibles)  : 2 652 621
Versions chargées (fait SCD2)       : 1 234 850
Communes                            : 302
```

Le nombre d'établissements **actifs** à une date donnée se lit ensuite dans
l'entrepôt (`analyse.sql`, filtre `is_current AND etat = 'A'`).

Script utilisé : `collect.py::collect()`. L'accès distant data.gouv, le chargement de httpfs, le filtre RGPD (`statutDiffusion = 'O'`) et le filtre périmètre (`substr(codeCommune,1,2) = '69'`) sont tous validés par l'exécution. En cas d'écart, vérifier dans l'ordre : URL du mois, nom des colonnes (peuvent changer entre publications), clause de filtre département.

## 6. Tests de régression

Une suite `pytest` (`tests.py`, 5 tests) vérifie la logique du pipeline sans dépendance réseau ni PostgreSQL : chaque test crée une petite table duckdb en mémoire avec des cas connus, applique la logique, et contrôle le résultat.

| Test | Ce qu'il vérifie |
|---|---|
| `test_filtre_rgpd` | le filtre RGPD ne garde que `statut = 'O'` |
| `test_filtre_departement` | le filtre ne garde que les communes du 69 |
| `test_date_trop_vieille` | une date antérieure à 1900 est bien repérée |
| `test_pas_de_doublon` | `dim_commune.code_commune` ne contient pas de doublon |
| `test_nn_present` | la tranche `NN` est bien présente et traitée comme non renseignée |

Lancer : `pytest tests.py -v`.

