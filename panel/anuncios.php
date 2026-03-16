<?php
require_once 'config.php';
requireLogin();

$db = getDB();
$success = $_GET['success'] ?? '';
$error = $_GET['error'] ?? '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'enviar_anuncio') {
    $mensaje = trim($_POST['mensaje'] ?? '');

    if ($mensaje === '') {
        $error = 'El mensaje no puede estar vacío.';
    } elseif (!BOT_MAIN_TOKEN) {
        $error = 'BOT_MAIN_TOKEN no está configurado en el servidor. Configúralo para enviar anuncios.';
    } else {
        $usuarios = $db->query("SELECT id, username, telegram_id FROM usuarios WHERE telegram_id IS NOT NULL")->fetchAll();
        $enviados = 0;
        $fallidos = 0;

        foreach ($usuarios as $u) {
            $ok = sendTelegramMessage($u['telegram_id'], "📢 *ANUNCIO OFICIAL*\n\n" . $mensaje);
            if ($ok) {
                $enviados++;
            } else {
                $fallidos++;
            }
        }

        header('Location: anuncios.php?success=' . urlencode("Anuncio enviado. Enviados: {$enviados}, Fallidos: {$fallidos}"));
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anuncios - Panel Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0f; color: #fff; line-height: 1.6; }

        .sidebar { position: fixed; left: 0; top: 0; width: 260px; height: 100vh; background: #12121a; border-right: 1px solid rgba(255,255,255,.1); display: flex; flex-direction: column; }
        .sidebar-header { padding: 24px 20px; border-bottom: 1px solid rgba(255,255,255,.1); }
        .logo { display: flex; align-items: center; gap: 12px; }
        .logo-icon { width: 40px; height: 40px; background: linear-gradient(135deg,#00ff88,#00cc6a); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: #000; }
        .logo-text { font-weight: 600; font-size: 1.1rem; }
        .nav-menu { list-style: none; padding: 16px 12px; flex: 1; }
        .nav-item { margin-bottom: 4px; }
        .nav-link { display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #a0a0b0; text-decoration: none; border-radius: 12px; transition: all .3s ease; }
        .nav-link:hover { background: #252530; color: #fff; }
        .nav-link.active { background: linear-gradient(135deg,rgba(0,255,136,.1),rgba(0,204,106,.1)); color: #00ff88; border: 1px solid rgba(0,255,136,.2); }
        .sidebar-footer { padding: 16px; border-top: 1px solid rgba(255,255,255,.1); }
        .admin-info { display: flex; align-items: center; gap: 10px; padding: 10px; background: #252530; border-radius: 12px; margin-bottom: 12px; font-size: .9rem; color: #a0a0b0; }
        .logout-btn { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; color: #ff4757; text-decoration: none; border-radius: 12px; transition: all .3s ease; font-size: .9rem; }
        .logout-btn:hover { background: rgba(255,71,87,.1); }

        .main-content { margin-left: 260px; padding: 32px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
        .page-title { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg,#00ff88,#00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .page-subtitle { color: #a0a0b0; margin-top: 4px; }

        .alert { padding: 14px 18px; border-radius: 12px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
        .alert-success { background: rgba(0,255,136,.1); border: 1px solid rgba(0,255,136,.2); color: #00ff88; }
        .alert-error { background: rgba(255,71,87,.1); border: 1px solid rgba(255,71,87,.2); color: #ff4757; }

        .card { background: #1a1a24; border: 1px solid rgba(255,255,255,.1); border-radius: 20px; padding: 24px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 8px; font-size: .9rem; color: #a0a0b0; }
        .form-control { width: 100%; padding: 12px 16px; background: #12121a; border: 1px solid rgba(255,255,255,.1); border-radius: 12px; color: #fff; font-size: 1rem; }
        textarea.form-control { min-height: 180px; resize: vertical; }
        .btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 12px; font-weight: 600; border: none; cursor: pointer; }
        .btn-primary { background: linear-gradient(135deg,#00ff88,#00cc6a); color: #000; }
        .hint { color: #8a8aa0; font-size: .9rem; margin-top: 8px; }
    </style>
</head>
<body>
    <nav class="sidebar">
        <div class="sidebar-header">
            <div class="logo"><span class="logo-icon">TX</span><span class="logo-text">Torres Shop</span></div>
        </div>
        <ul class="nav-menu">
            <li class="nav-item"><a href="dashboard.php" class="nav-link"><i class="fas fa-home"></i><span>Dashboard</span></a></li>
            <li class="nav-item"><a href="recargas.php" class="nav-link"><i class="fas fa-wallet"></i><span>Recargas</span></a></li>
            <li class="nav-item"><a href="productos.php" class="nav-link"><i class="fas fa-key"></i><span>Licencias</span></a></li>
            <li class="nav-item"><a href="usuarios.php" class="nav-link"><i class="fas fa-users"></i><span>Usuarios</span></a></li>
            <li class="nav-item"><a href="metodos_pago.php" class="nav-link"><i class="fas fa-credit-card"></i><span>Métodos de Pago</span></a></li>
            <li class="nav-item"><a href="anuncios.php" class="nav-link active"><i class="fas fa-bullhorn"></i><span>Anuncios</span></a></li>
        </ul>
        <div class="sidebar-footer">
            <div class="admin-info"><i class="fas fa-user-shield"></i><span><?= e($_SESSION['admin_user']) ?></span></div>
            <a href="logout.php" class="logout-btn"><i class="fas fa-sign-out-alt"></i>Cerrar Sesión</a>
        </div>
    </nav>

    <main class="main-content">
        <div class="page-header">
            <div>
                <h1 class="page-title">Anuncios</h1>
                <p class="page-subtitle">Envía anuncios masivos a usuarios vinculados en Telegram</p>
            </div>
        </div>

        <?php if ($success): ?>
            <div class="alert alert-success"><i class="fas fa-check-circle"></i><?= e($success) ?></div>
        <?php endif; ?>
        <?php if ($error): ?>
            <div class="alert alert-error"><i class="fas fa-exclamation-circle"></i><?= e($error) ?></div>
        <?php endif; ?>

        <div class="card">
            <form method="POST">
                <input type="hidden" name="action" value="enviar_anuncio">
                <div class="form-group">
                    <label>Mensaje del anuncio</label>
                    <textarea name="mensaje" class="form-control" required placeholder="Ejemplo:
🚀 Nuevo producto disponible: Combo Premium
✅ Ya puedes comprarlo en el bot."></textarea>
                    <p class="hint">Este anuncio se enviará a todos los usuarios con Telegram vinculado.</p>
                </div>
                <button type="submit" class="btn btn-primary"><i class="fas fa-paper-plane"></i> Enviar Anuncio</button>
            </form>
        </div>
    </main>
</body>
</html>
