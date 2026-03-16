<?php
/**
 * Configuración del Panel Admin - Torres Shop
 * Conexión a PostgreSQL (Railway) y configuración de sesión
 */

// Iniciar sesión
session_start();

// Configuración de Base de Datos (PostgreSQL en Railway)
define('DB_HOST', 'switchback.proxy.rlwy.net');
define('DB_PORT', '12748');
define('DB_NAME', 'railway');
define('DB_USER', 'postgres');
define('DB_PASS', 'vdXRWNDASnlinYyBUgypxIMNDixdymnW');

// Credenciales del panel admin
define('ADMIN_USERNAME', 'admin');
define('ADMIN_PASSWORD', 'admin123'); // CAMBIA ESTO en producción

// Token del bot principal (para anuncios desde el panel)
// Recomendado: exportar BOT_MAIN_TOKEN en el entorno de Apache/PHP-FPM
define('BOT_MAIN_TOKEN', getenv('BOT_MAIN_TOKEN') ?: '');

// Conexión PDO
function getDB() {
    static $pdo = null;
    
    if ($pdo === null) {
        try {
            $dsn = "pgsql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME;
            $pdo = new PDO($dsn, DB_USER, DB_PASS, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false
            ]);
        } catch (PDOException $e) {
            die("Error de conexión: " . $e->getMessage());
        }
    }
    
    return $pdo;
}

// Verificar si está logueado
function requireLogin() {
    if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
        header('Location: login.php');
        exit;
    }
}

// Función para escapar HTML
function e($string) {
    return htmlspecialchars($string, ENT_QUOTES, 'UTF-8');
}

// Función para formatear fechas
function formatDate($date) {
    if (!$date) return 'N/A';
    $dt = new DateTime($date);
    return $dt->format('d/m/Y H:i');
}

// Función para formatear moneda
function formatMoney($amount) {
    return '$' . number_format($amount, 2);
}

// Enviar mensaje a Telegram usando Bot API
function sendTelegramMessage($chatId, $message) {
    if (!BOT_MAIN_TOKEN) {
        return false;
    }

    $url = 'https://api.telegram.org/bot' . BOT_MAIN_TOKEN . '/sendMessage';
    $payload = [
        'chat_id' => $chatId,
        'text' => $message,
        'parse_mode' => 'Markdown'
    ];

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($payload));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    $result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return $result !== false && $httpCode >= 200 && $httpCode < 300;
}
?>
