from datetime import datetime

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