-- =============================================================================
-- Migración para la subida automática (IA-CORRECTOR-MANOS)
-- Ejecutar UNA vez en phpMyAdmin sobre nofxdyfx_texas_holdem_cash_table.
-- =============================================================================

-- 1. Columnas nuevas en manos_review
--    hand_id     -> nº de mano de PT4 (UNIQUE: evita subir la misma mano dos veces)
--    analisis_ia -> pre-análisis de Ollama (Fase 4)
ALTER TABLE manos_review
    ADD COLUMN hand_id VARCHAR(32) NULL,
    ADD COLUMN analisis_ia TEXT NULL,
    ADD UNIQUE KEY uq_manos_review_hand_id (hand_id);

-- 2. Categorías nuevas para los spots que no tenían
INSERT IGNORE INTO categorias (id, nombre) VALUES
    (10, 'BlindWar'),
    (11, 'OOP'),
    (12, 'Review');

-- Comprobación
SELECT * FROM categorias ORDER BY id;
SHOW COLUMNS FROM manos_review;
