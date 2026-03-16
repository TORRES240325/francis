<?php
require_once 'config.php';
requireLogin();

$db = getDB();
$success = $_GET['success'] ?? '';
$error = $_GET['error'] ?? '';
$status_filter = $_GET['status_filter'] ?? null;

// Procesar acciones
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        if (isset($_POST['action'])) {
            if ($_POST['action'] === 'aprobar') {
                $req_id = intval($_POST['req_id']);
                
                $db->beginTransaction();
                
                $recarga = $db->prepare("SELECT * FROM topup_requests WHERE id = ? AND status = 'pending'");
                $recarga->execute([$req_id]);
                $r = $recarga->fetch();
                
                if ($r) {
                    $db->prepare("UPDATE usuarios SET saldo = saldo + ? WHERE id = ?")->execute([$r['monto'], $r['usuario_id']]);
                    $db->prepare("UPDATE topup_requests SET status = 'approved', fecha_resolucion = NOW() WHERE id = ?")->execute([$req_id]);
                    $db->commit();
                    header('Location: recargas.php?success=Recarga aprobada');
                    exit;
                }
                $db->rollBack();
            } elseif ($_POST['action'] === 'rechazar') {
                $req_id = intval($_POST['req_id']);
                $db->prepare("UPDATE topup_requests SET status = 'rejected', fecha_resolucion = NOW() WHERE id = ?")->execute([$req_id]);
                header('Location: recargas.php?success=Recarga rechazada');
                exit;
            }
        }
    } catch (PDOException $e) {
        if ($db->inTransaction()) $db->rollBack();
        $error = 'Error: ' . $e->getMessage();
    }
}

// Obtener estadísticas
$pendientes = $db->query("SELECT COUNT(*) FROM topup_requests WHERE status = 'pending'")->fetchColumn();
$aprobadas = $db->query("SELECT COUNT(*) FROM topup_requests WHERE status = 'approved'")->fetchColumn();
$rechazadas = $db->query("SELECT COUNT(*) FROM topup_requests WHERE status = 'rejected'")->fetchColumn();

// Obtener recargas
$query = "SELECT tr.*, u.username, pm.nombre as metodo_nombre 
          FROM topup_requests tr 
          LEFT JOIN usuarios u ON tr.usuario_id = u.id 
          LEFT JOIN payment_methods pm ON tr.metodo_pago_id = pm.id";
if ($status_filter) {
    $query .= " WHERE tr.status = ?";
}
$query .= " ORDER BY tr.id DESC";

$stmt = $db->prepare($query);
if ($status_filter) {
    $stmt->execute([$status_filter]);
} else {
    $stmt->execute();
}
$recargas = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Recargas - Panel Admin</title>
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
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; flex-wrap: wrap; gap: 16px; }
        .page-title { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .page-subtitle { color: #a0a0b0; margin-top: 4px; }
        
        .stats-inline { display: flex; gap: 16px; }
        .stat-box { text-align: center; padding: 12px 24px; background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; min-width: 100px; }
        .stat-box.pending { border-color: rgba(253, 203, 110, 0.3); background: rgba(253, 203, 110, 0.05); }
        .stat-box.approved { border-color: rgba(0, 255, 136, 0.3); background: rgba(0, 255, 136, 0.05); }
        .stat-box.rejected { border-color: rgba(255, 71, 87, 0.3); background: rgba(255, 71, 87, 0.05); }
        .stat-box .stat-number { display: block; font-size: 1.5rem; font-weight: 700; }
        .stat-box.pending .stat-number { color: #fdcb6e; }
        .stat-box.approved .stat-number { color: #00ff88; }
        .stat-box.rejected .stat-number { color: #ff4757; }
        .stat-box .stat-label { font-size: 0.75rem; color: #606070; text-transform: uppercase; }
        
        .filters-bar { display: flex; gap: 12px; margin-bottom: 24px; }
        .filter-btn { padding: 10px 20px; background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #a0a0b0; text-decoration: none; font-size: 0.9rem; transition: all 0.3s ease; }
        .filter-btn:hover { border-color: #00ff88; color: #fff; }
        .filter-btn.active { background: rgba(0, 255, 136, 0.1); border-color: #00ff88; color: #00ff88; }
        
        .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 20px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; cursor: pointer; border: none; transition: all 0.3s ease; text-decoration: none; }
        .btn-primary { background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); color: #000; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3); }
        .btn-danger { background: linear-gradient(135deg, #ff4757 0%, #cc3645 100%); color: white; }
        .btn-sm { padding: 6px 14px; font-size: 0.8rem; }
        
        .alert { padding: 14px 18px; border-radius: 12px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
        .alert-success { background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.2); color: #00ff88; }
        .alert-error { background: rgba(255, 71, 87, 0.1); border: 1px solid rgba(255, 71, 87, 0.2); color: #ff4757; }
        
        .table-container { background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; overflow: hidden; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        th { background: #252530; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #a0a0b0; }
        tr:hover td { background: #252530; }
        
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-transform: capitalize; }
        .status-pending { background: rgba(253, 203, 110, 0.15); color: #fdcb6e; }
        .status-approved { background: rgba(0, 255, 136, 0.15); color: #00ff88; }
        .status-rejected { background: rgba(255, 71, 87, 0.15); color: #ff4757; }
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
            <li class="nav-item"><a href="recargas.php" class="nav-link active"><i class="fas fa-wallet"></i><span>Recargas</span></a></li>
            <li class="nav-item"><a href="productos.php" class="nav-link"><i class="fas fa-key"></i><span>Licencias</span></a></li>
            <li class="nav-item"><a href="usuarios.php" class="nav-link"><i class="fas fa-users"></i><span>Usuarios</span></a></li>
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
                <h1 class="page-title">Gestión de Recargas</h1>
                <p class="page-subtitle">Aprueba o rechaza solicitudes de recarga de saldo</p>
            </div>
            <div class="stats-inline">
                <div class="stat-box pending">
                    <span class="stat-number"><?= $pendientes ?></span>
                    <span class="stat-label">Pendientes</span>
                </div>
                <div class="stat-box approved">
                    <span class="stat-number"><?= $aprobadas ?></span>
                    <span class="stat-label">Aprobadas</span>
                </div>
                <div class="stat-box rejected">
                    <span class="stat-number"><?= $rechazadas ?></span>
                    <span class="stat-label">Rechazadas</span>
                </div>
            </div>
        </div>
        
        <div class="filters-bar">
            <a href="recargas.php" class="filter-btn <?= !$status_filter ? 'active' : '' ?>">Todas</a>
            <a href="recargas.php?status_filter=pending" class="filter-btn <?= $status_filter === 'pending' ? 'active' : '' ?>">Pendientes</a>
            <a href="recargas.php?status_filter=approved" class="filter-btn <?= $status_filter === 'approved' ? 'active' : '' ?>">Aprobadas</a>
            <a href="recargas.php?status_filter=rejected" class="filter-btn <?= $status_filter === 'rejected' ? 'active' : '' ?>">Rechazadas</a>
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
                        <th>Usuario</th>
                        <th>Monto</th>
                        <th>Método de Pago</th>
                        <th>Referencia</th>
                        <th>Estado</th>
                        <th>Fecha</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (count($recargas) > 0): ?>
                        <?php foreach ($recargas as $r): ?>
                        <tr>
                            <td>#<?= $r['id'] ?></td>
                            <td>
                                <strong><?= e($r['username'] ?? 'N/A') ?></strong>
                                <br><small style="color: #666;">ID: <?= $r['usuario_id'] ?></small>
                            </td>
                            <td><span style="color: #00ff88; font-weight: 600;"><?= formatMoney($r['monto']) ?></span></td>
                            <td><?= e($r['metodo_nombre'] ?? 'N/A') ?></td>
                            <td>
                                <code style="background: rgba(0,0,0,0.3); padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">
                                    <?= e($r['referencia'] ?? 'N/A') ?>
                                </code>
                            </td>
                            <td><span class="status-badge status-<?= $r['status'] ?>"><?= e($r['status']) ?></span></td>
                            <td><?= formatDate($r['fecha_creacion']) ?></td>
                            <td>
                                <?php if ($r['status'] === 'pending'): ?>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="action" value="aprobar">
                                    <input type="hidden" name="req_id" value="<?= $r['id'] ?>">
                                    <button type="submit" class="btn btn-sm btn-primary" style="margin-right: 8px;">
                                        <i class="fas fa-check"></i> Aprobar
                                    </button>
                                </form>
                                <form method="POST" style="display: inline;">
                                    <input type="hidden" name="action" value="rechazar">
                                    <input type="hidden" name="req_id" value="<?= $r['id'] ?>">
                                    <button type="submit" class="btn btn-sm btn-danger">
                                        <i class="fas fa-times"></i> Rechazar
                                    </button>
                                </form>
                                <?php else: ?>
                                <span style="color: #666; font-size: 0.85rem;">
                                    <?= formatDate($r['fecha_resolucion']) ?>
                                </span>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <tr>
                            <td colspan="8" style="text-align: center; color: #606070; padding: 40px;">
                                <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 10px; display: block;"></i>
                                No hay recargas <?= $status_filter ? e($status_filter) : '' ?>
                            </td>
                        </tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>
