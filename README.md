# Observatoire SIRENE

ETL permettant de charger les données historiques SIRENE à partir de fichiers Parquet dans une base PostgreSQL en construisant un modèle décisionnel (dimensions et faits).

## Fonctionnalités

- Lecture des fichiers Parquet via DuckDB
- Filtrage et transformation des données en Python
- Chargement des dimensions
- Chargement de la table de faits
- Gestion des doublons
- Chargement incrémental

## Architecture

```
                +----------------------+
                |  Fichiers Parquet     |
                +----------+-----------+
                           |
                           v
                     DuckDB (lecture)
                           |
                           v
                     collect.py
                           |
                           v
                      clean.py
                           |
                           v
                       load.py
                           |
                           v
                      PostgreSQL
```
## Structure du projet

```
observatoire-sirene/
│
├── README.md
├── requirements.txt
├── .env
├── .gitignore
├── schema.sql
├── analyse.sql
│
├── DECISIONS.md
│── FAISABILITE.md
│
├── data/
│   └── Les fichiers parquets
│
│── test.ipynb
│
│── main.py
│── collect.py
│── clean.py
│── quality.py
│── load.py
│── load_alt.py
│── main_alt.py
│
├──test_pipeline.py
│
└── local_data/
```

## Prérequis

- Python 3.14+
- PostgreSQL 18+
- DuckDB

## Installation

Créer un environnement virtuel :

```bash
python -m venv env
```

Activer l'environnement :

Windows :

```bash
env\Scripts\activate
```

Linux/macOS :

```bash
source env/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Configuration

Créer un fichier `.env` :

```text
DATABASE_URL=postgresql://user:password@localhost:5432/my_database
```
## Utilisation

Lancer le chargement :

```bash
python main.py
```