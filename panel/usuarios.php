<?php
require_once 'config.php';
requireLogin();

$db = getDB();
$success = $_GET['success'] ?? '';
$error = $_GET['error'] ?? '';

// Procesar acciones
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['action'])) {
        try {
            if ($_POST['action'] === 'crear') {
                $es_admin = (!empty($_POST['es_admin']) && $_POST['es_admin'] === 'true') ? 'true' : 'false';
                $stmt = $db->prepare("INSERT INTO usuarios (username, login_key, saldo, es_admin) VALUES (?, ?, ?, CAST(? AS boolean))");
                $stmt->execute([
                    $_POST['username'],
                    $_POST['login_key'],
                    floatval($_POST['saldo']),
                    $es_admin
                ]);
                header('Location: usuarios.php?success=Usuario creado exitosamente');
                exit;
            } elseif ($_POST['action'] === 'ajustar_saldo') {
                $stmt = $db->prepare("UPDATE usuarios SET saldo = saldo + ? WHERE id = ?");
                $stmt->execute([floatval($_POST['monto']), intval($_POST['user_id'])]);
                header('Location: usuarios.php?success=Saldo ajustado');
                exit;
            }
        } catch (PDOException $e) {
            $error = 'Error: ' . $e->getMessage();
        }
    }
}

// Obtener usuarios
$usuarios = $db->query("SELECT * FROM usuarios ORDER BY id DESC")->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Usuarios - Panel Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0f; color: #fff; line-height: 1.6; }
        
        .sidebar { position: fixed; left: 0; top: 0; width: 260px; height: 100vh; background: #12121a; border-right: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-direction: column; }
        .sidebar-header { padding: 24px 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        .logo { display: flex; align-items: center; gap: 12px; }
        .logo-icon { width: 40px; height: 40px; background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: #000; }
        .logo-text { font-weight: 600; font-size: 1.1rem; }
        .nav-menu { list-style: none; padding: 16px 12px; flex: 1; }
        .nav-item { margin-bottom: 4px; }
        .nav-link { display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #a0a0b0; text-decoration: none; border-radius: 12px; transition: all 0.3s ease; }
        .nav-link:hover { background: #252530; color: #fff; }
        .nav-link.active { background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 204, 106, 0.1) 100%); color: #00ff88; border: 1px solid rgba(0, 255, 136, 0.2); }
        .sidebar-footer { padding: 16px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
        .admin-info { display: flex; align-items: center; gap: 10px; padding: 10px; background: #252530; border-radius: 12px; margin-bottom: 12px; font-size: 0.9rem; color: #a0a0b0; }
        .logout-btn { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; color: #ff4757; text-decoration: none; border-radius: 12px; transition: all 0.3s ease; font-size: 0.9rem; }
        .logout-btn:hover { background: rgba(255, 71, 87, 0.1); }
        
        .main-content { margin-left: 260px; padding: 32px; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
        .page-title { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .page-subtitle { color: #a0a0b0; margin-top: 4px; }
        
        .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 20px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; cursor: pointer; border: none; transition: all 0.3s ease; text-decoration: none; }
        .btn-primary { background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); color: #000; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3); }
        .btn-secondary { background: #252530; color: #fff; border: 1px solid rgba(255, 255, 255, 0.1); }
        .btn-sm { padding: 6px 14px; font-size: 0.8rem; }
        
        .alert { padding: 14px 18px; border-radius: 12px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
        .alert-success { background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.2); color: #00ff88; }
        .alert-error { background: rgba(255, 71, 87, 0.1); border: 1px solid rgba(255, 71, 87, 0.2); color: #ff4757; }
        
        .table-container { background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; overflow: hidden; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        th { background: #252530; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #a0a0b0; }
        tr:hover td { background: #252530; }
        
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
        .saldo-badge { display: inline-block; padding: 6px 14px; background: linear-gradient(135deg, rgba(0,255,136,0.15) 0%, rgba(0,204,106,0.15) 100%); border: 1px solid rgba(0,255,136,0.3); border-radius: 20px; font-weight: 600; color: #00ff88; }
        
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.8); display: none; align-items: center; justify-content: center; z-index: 2000; }
        .modal-overlay.active { display: flex; }
        .modal { background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto; }
        .modal-header { padding: 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        .modal-header h2 { font-size: 1.3rem; }
        .modal-body { padding: 24px; }
        .modal-footer { padding: 20px 24px; border-top: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: flex-end; gap: 12px; }
        
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-size: 0.9rem; color: #a0a0b0; }
        .form-control { width: 100%; padding: 12px 16px; background: #12121a; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #fff; font-size: 1rem; transition: all 0.3s ease; }
        .form-control:focus { outline: none; border-color: #00ff88; box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1); }
    </style>
</head>
<body>
    <nav class="sidebar">
        <div class="sidebar-header">
            <div class="logo">
                <span class="logo-icon">TX</span>
                <span class="logo-text">Torres Shop</span>
            </div>
        </div>
        <ul class="nav-menu">
            <li class="nav-item"><a href="dashboard.php" class="nav-link"><i class="fas fa-home"></i><span>Dashboard</span></a></li>
            <li class="nav-item"><a href="recargas.php" class="nav-link"><i class="fas fa-wallet"></i><span>Recargas</span></a></li>
            <li class="nav-item"><a href="productos.php" class="nav-link"><i class="fas fa-key"></i><span>Licencias</span></a></li>
            <li class="nav-item"><a href="usuarios.php" class="nav-link active"><i class="fas fa-users"></i><span>Usuarios</span></a></li>
            <li class="nav-item"><a href="metodos_pago.php" class="nav-link"><i class="fas fa-credit-card"></i><span>Métodos de Pago</span></a></li>
        </ul>
        <div class="sidebar-footer">
            <div class="admin-info"><i class="fas fa-user-shield"></i><span><?= e($_SESSION['admin_user']) ?></span></div>
            <a href="logout.php" class="logout-btn"><i class="fas fa-sign-out-alt"></i>Cerrar Sesión</a>
        </div>
    </nav>
    
    <main class="main-content">
        <div class="page-header">
            <div>
                <h1 class="page-title">Usuarios</h1>
                <p class="page-subtitle">Buscar, ver métricas y ajustar saldo de usuarios</p>
            </div>
            <button class="btn btn-primary" onclick="openModal('createUserModal')">
                <i class="fas fa-plus"></i> Crear Usuario
            </button>
        </div>
        
        <?php if ($success): ?>
        <div class="alert alert-success"><i class="fas fa-check-circle"></i><?= e($success) ?></div>
        <?php endif; ?>
        
        <?php if ($error): ?>
        <div class="alert alert-error"><i class="fas fa-exclamation-circle"></i><?= e($error) ?></div>
        <?php endif; ?>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Telegram ID</th>
                        <th>Saldo</th>
                        <th>Rol</th>
                        <th>Registro</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($usuarios as $u): ?>
                    <tr>
                        <td>#<?= $u['id'] ?></td>
                        <td><strong><?= e($u['username']) ?></strong></td>
                        <td><?= $u['telegram_id'] ?? 'No vinculado' ?></td>
                        <td><span class="saldo-badge"><?= formatMoney($u['saldo']) ?></span></td>
                        <td>
                            <?php if ($u['es_admin']): ?>
                            <span class="status-badge" style="background: rgba(0,255,136,0.15); color: #00ff88;">Admin</span>
                            <?php else: ?>
                            <span class="status-badge" style="background: rgba(116,185,255,0.15); color: #74b9ff;">Usuario</span>
                            <?php endif; ?>
                        </td>
                        <td><?= formatDate($u['fecha_registro']) ?></td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="openAdjustModal(<?= $u['id'] ?>, '<?= e($u['username']) ?>', <?= $u['saldo'] ?>)">
                                <i class="fas fa-coins"></i> Ajustar Saldo
                            </button>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    </main>
    
    <!-- Modal Crear Usuario -->
    <div id="createUserModal" class="modal-overlay">
        <div class="modal">
            <div class="modal-header"><h2><i class="fas fa-user-plus"></i> Crear Nuevo Usuario</h2></div>
            <form method="POST">
                <input type="hidden" name="action" value="crear">
                <div class="modal-body">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="username" class="form-control" required placeholder="ej: cliente123">
                    </div>
                    <div class="form-group">
                        <label>Login Key / Contraseña</label>
                        <input type="text" name="login_key" class="form-control" required placeholder="Clave para el bot">
                    </div>
                    <div class="form-group">
                        <label>Saldo Inicial ($)</label>
                        <input type="number" step="0.01" name="saldo" class="form-control" value="0" placeholder="0.00">
                    </div>
                    <div class="form-group">
                        <label><input type="checkbox" name="es_admin" value="true"> Es Administrador</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('createUserModal')">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Crear Usuario</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Modal Ajustar Saldo -->
    <div id="adjustSaldoModal" class="modal-overlay">
        <div class="modal">
            <div class="modal-header"><h2><i class="fas fa-coins"></i> Ajustar Saldo</h2></div>
            <form id="adjustForm" method="POST">
                <input type="hidden" name="action" value="ajustar_saldo">
                <input type="hidden" name="user_id" id="adjustUserId">
                <div class="modal-body">
                    <p style="margin-bottom: 20px;">
                        Usuario: <strong id="adjustUsername"></strong><br>
                        Saldo actual: <span style="color: #00ff88;">$<span id="currentSaldo"></span></span>
                    </p>
                    <div class="form-group">
                        <label>Monto a ajustar (positivo para agregar, negativo para restar)</label>
                        <input type="number" step="0.01" name="monto" class="form-control" required placeholder="ej: 10.00 o -5.00">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('adjustSaldoModal')">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Ajustar Saldo</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function openModal(id) { document.getElementById(id).classList.add('active'); }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        function openAdjustModal(userId, username, currentSaldo) {
            document.getElementById('adjustUserId').value = userId;
            document.getElementById('adjustUsername').textContent = username;
            document.getElementById('currentSaldo').textContent = currentSaldo.toFixed(2);
            openModal('adjustSaldoModal');
        }
        window.onclick = function(event) {
            if (event.target.classList.contains('modal-overlay')) {
                event.target.classList.remove('active');
            }
        }
    </script>
</body>
</html>
