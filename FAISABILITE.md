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
| `activitePrincipaleEtablissement` | oui (voir historique) | non repris ici, source = historique |
| `etatAdministratifEtablissement` | oui (voir historique) | non repris ici, source = historique |
| `statutDiffusionEtablissement` | — | filtre RGPD |
| `denominationUsuelleEtablissement` / `enseigne*` | oui | **non suivi** (hors contrat, cf. §4) |

⚠️ Point clé : `code_commune` et `code_tranche` n'existent que dans le stock, donc on ne connaît que leur valeur **actuelle** — impossible de savoir où était implanté un établissement en 2019 si son adresse a changé depuis.

### StockEtablissementHistorique (~0,87 Go, 95,3 M périodes au national)
Une ligne par établissement **et par période de validité** `[dateDebut, dateFin[`.

| Colonne | Historisée ? | Usage prévu |
|---|---|---|
| `siret` | — | clé du fait |
| `dateDebut` / `dateFin` | oui, par définition | `valid_from` / `valid_to` |
| `etatAdministratifEtablissement` (A/F) | oui | attribut du fait |
| `activitePrincipaleEtablissement` | oui | `dim_activite` (FK) |
| `nomenclatureActivitePrincipaleEtablissement` | oui | `dim_activite.nomenclature` |
| `denominationUsuelleEtablissement` | oui | **non suivi** (le contrat ignore le nom) |

## 2. Volumétrie

| Périmètre | Établissements diffusibles (estim.) | Périodes historisées (estim.) |
|---|---|---|
| Rhône (69) | ~1,20 M | ~2,65 M |
| Région ARA (12 dépt.) | À mesurer — ordre de grandeur ×6 à ×8 | idem |
| France entière | 43,7 M (stock) | 95,3 M (historique) |

À vérifier avec `collecte.py` (fonction `controle_rapide`) une fois l'accès distant validé. La projection région/France sert à anticiper le brief 2 (dbt + passage à l'échelle) : au-delà du Rhône, `pandas` en mémoire complète n'est plus une option, `duckdb` en lecture colonnes reste nécessaire.


## 3. Qualité des données

- **`NN`** : tranche d'effectifs non renseignée — fréquente, à ne pas confondre
  avec une vraie valeur ; à exclure ou isoler des agrégats d'emploi (Partie 4,
  question sur la répartition par tranche).
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

  Soit environ 102 lignes sur 2,65 M (**~0,004 %**). 


## 4. RGPD

`statutDiffusionEtablissement` encode la diffusibilité :
- `'O'` : diffusible
- `'P'` : diffusion restreinte (entrepreneur individuel ayant demandé le masquage — la fiche peut porter un nom de personne physique)

**Règle appliquée** : ne conserver que les `'O'`, filtrées dès la collecte (avant toute autre transformation), et ne jamais reprendre de colonne de nom/dénomination dans l'entrepôt final — cohérent avec le contrat qui ne suit pas la dénomination.

## 5. Preuve de faisabilité technique

Chiffre choisi : **nombre d'établissements actifs et diffusibles du Rhône**, calculé via `duckdb` + `httpfs` en lecture distante sur les Parquet SIRENE (sans téléchargement complet, lecture en colonnes).

```
Établissements (stock, diffusibles) : [à compléter après exécution]
  dont actifs                        : [à compléter — attendu ≈ 430 000]
Périodes (historique, diffusibles)  : [à compléter]
```

Script utilisé : `collecte.py::controle_rapide()`. Si le chiffre est proche de l'ordre de grandeur attendu (~430 000 actifs) → chaîne technique validée (accès data.gouv, httpfs, filtre RGPD, filtre périmètre). Sinon, vérifier dans l'ordre : URL du mois, nom des colonnes (peuvent changer entre publications), clause de filtre département.

---
*À compléter avec les chiffres réels avant la revue de sprint. Backlog priorisé en pièce jointe (Google Sheets).*