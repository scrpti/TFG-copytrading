CREATE TABLE IF NOT EXISTS traders (
    cid               BIGINT PRIMARY KEY,
    username          TEXT NOT NULL,
    plataforma        TEXT NOT NULL DEFAULT 'etoro',
    primera_vez_visto DATE NOT NULL,
    ultima_vez_visto  DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS rendimientos_diarios (
    cid               BIGINT NOT NULL REFERENCES traders(cid),
    fecha             DATE NOT NULL,
    rentabilidad      DOUBLE PRECISION NOT NULL,
    PRIMARY KEY(cid, fecha)
);

SELECT create_hypertable('rendimientos_diarios', by_range('fecha'), if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS snapshots_ranking (
    fecha             DATE NOT NULL,
    cid               BIGINT NOT NULL REFERENCES traders(cid),
    rentabilidad      DOUBLE PRECISION,
    riesgo            INTEGER,
    copiadores        INTEGER,
    aum               DOUBLE PRECISION,
    datos             JSONB NOT NULL,
    PRIMARY KEY(cid, fecha)
);

SELECT create_hypertable('snapshots_ranking', by_range('fecha'), if_not_exists => TRUE);