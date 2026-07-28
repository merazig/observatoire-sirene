import duckdb


def check_dates_aberrantes(con, historique):
    con.register("historique", historique)
    bornes = con.sql("""
        SELECT MIN(dateDebut) AS debut_min,
               MAX(dateDebut) AS debut_max,
               MIN(dateFin)   AS fin_min,
               MAX(dateFin)   AS fin_max,
               COUNT(*)       AS total_lignes
        FROM historique
    """)
    aberrations = con.sql("""
        SELECT
            COUNT(*) FILTER (WHERE dateDebut < DATE '1900-01-01') AS debut_trop_vieux,
            COUNT(*) FILTER (WHERE dateDebut > CURRENT_DATE)      AS debut_futur,
            COUNT(*) FILTER (WHERE dateFin   > CURRENT_DATE)      AS fin_futur,
            COUNT(*) FILTER (WHERE dateFin   < dateDebut)         AS fin_avant_debut
        FROM historique
    """)
    return (bornes, aberrations)