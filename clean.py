import pandas as pd
from datetime import date 


def clean_date(date_):
    date_list = str(date_).split('-')
    if len(date_list) != 3:
        return "0"
    annee = int(date_list[0])
    mois = int(date_list[1])
    trimestre = 0
    if mois in (1,2,3):
        trimestre = 1
    elif mois in (4,5,6):
        trimestre = 2
    elif mois in (7,8,9):
        trimestre = 3
    elif mois in (10,11,12):
        trimestre = 4
    return (date_, annee, trimestre, mois)

def construire_dim_tranche_effectifs():
  
    tranches = {
        "NN": "non renseigné",
        "00": "0 salarié",
        "01": "1-2",
        "02": "3-5",
        "03": "6-9",
        "11": "10-19",
        "12": "20-49",
        "21": "50-99",
        "22": "100-199",
        "31": "200-249",
        "32": "250-499",
        "41": "500-999",
        "42": "1000-1999",
        "51": "2000-4999",
        "52": "5000-9999",
        "53": "10000+",
    }

    donnees = pd.DataFrame({
        "code_tranche": list(tranches.keys()),
        "libelle": list(tranches.values()),
    })
    return donnees

def fait_etablissement(stock,historique,DEPT):
        ds=stock.df()
        dh=historique.df()
        dh = dh.sort_values(["siret", "dateDebut"])
        dh=dh[((dh.dateDebut>"1900-01-01")&(dh.dateDebut<str(date.today()))) |(dh.dateDebut.isna()) ]
        dh=dh[((dh.dateFin>"1900-01-01")&(dh.dateFin<str(date.today()))) ]                                   
        dh["cle"] = dh["code_ape"].fillna("?") + "|" + dh["etat"].fillna("?")
        dh["cle_prec"] = dh.groupby("siret")["cle"].shift(1) 
        fait = dh[dh["cle"] != dh["cle_prec"]].copy() 
        fait["valid_from"] = fait["dateDebut"]
        fait["valid_to"]   = fait.groupby("siret")["valid_from"].shift(-1)
        fait["is_current"] = fait["valid_to"].isna()
        historique=fait[['siret','dateDebut','dateFin','is_current','code_ape','etat']]
        ds = ds.drop(columns=['code_ape'], errors='ignore')
        fait_f=historique.merge(ds,on ='siret')
        fait_final = fait_f[
            [
                'siret',
                'dateDebut',
                'dateFin',
                'is_current',
                'code_commune',
                'code_ape',
                'tranche_effectifs',
                'etat'
            ]
        ]
        fait_final.to_parquet(f"data/fait_etablissement_version_{DEPT}.parquet")
        path = f"data/fait_etablissement_version_{DEPT}.parquet"
        return path
        
def dim_activite(con, historique):
    con.register("historique", historique)

    return con.sql("""
        SELECT DISTINCT
            code_ape,
            nomenclature_ape AS nomenclature
        FROM historique
        WHERE code_ape IS NOT NULL
    """).df()

