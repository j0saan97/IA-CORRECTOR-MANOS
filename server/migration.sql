-- Columnas nuevas en manos_review
ALTER TABLE manos_review
    ADD COLUMN hand_id VARCHAR(32) NULL,
    ADD COLUMN analisis_ia TEXT NULL,
    ADD UNIQUE KEY uq_manos_review_hand_id (hand_id);
