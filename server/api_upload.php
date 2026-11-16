<?php
// Endpoint de subida automática (protegido con cabecera X-Api-Token).
// TODO: validar token (hash_equals), validar imagen, rechazar hand_id duplicado (409),
//       guardar en uploads/, INSERT en manos_review y enlazar categoría por nombre.
require __DIR__ . '/config_api.php';
