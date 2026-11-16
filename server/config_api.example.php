<?php
// Copiar como config_api.php DIRECTAMENTE en el servidor. Nunca subirlo al repo.
const API_TOKEN = 'CAMBIAR';

$pdo = new PDO(
    'mysql:host=localhost;dbname=nofxdyfx_texas_holdem_cash_table;charset=utf8mb4',
    'USUARIO',
    'PASSWORD',
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
);
