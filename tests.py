import duckdb

# TEST 1 — le filtre RGPD qui ne devrait garder que les 'O'
def test_filtre_rgpd():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE stock AS SELECT * FROM (VALUES
            ('001', 'O'),
            ('002', 'O'),
            ('003', 'P')
        ) AS t(siret, statut)
    """)
    nb = con.sql("SELECT COUNT(*) FROM stock WHERE statut = 'O'").fetchone()[0]
    assert nb == 2

# TEST 2 — le filtre département ne garde que le 69
def test_filtre_departement():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE stock AS SELECT * FROM (VALUES
            ('69123'),
            ('69381'),
            ('75001')
        ) AS t(code_commune)
    """)
    nb = con.sql("""
        SELECT COUNT(*) FROM stock
        WHERE substr(code_commune, 1, 2) = '69'
    """).fetchone()[0]
    assert nb == 2   

# TEST 3 — on repère une date trop vieille (avant 1900)
def test_date_trop_vieille():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE historique AS SELECT * FROM (VALUES
            (DATE '2019-01-01'),
            (DATE '0004-01-03')
        ) AS t(dateDebut)
    """)
    nb = con.sql("""
        SELECT COUNT(*) FROM historique
        WHERE dateDebut < DATE '1900-01-01'
    """).fetchone()[0]
    assert nb == 1   

# TEST 4 — pas de doublon dans dim_commune
def test_pas_de_doublon():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE dim_commune AS SELECT * FROM (VALUES
            ('69123'),
            ('69381')
        ) AS t(code_commune)
    """)
    total = con.sql("SELECT COUNT(*) FROM dim_commune").fetchone()[0]
    distincts = con.sql("SELECT COUNT(DISTINCT code_commune) FROM dim_commune").fetchone()[0]
    assert total == distincts   