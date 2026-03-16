<?php
require_once 'config.php';
requireLogin();

$db = getDB();
$success = $_GET['success'] ?? '';
$error = $_GET['error'] ?? '';

// Procesar limpieza de base de datos
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'limpiar_db') {
    try {
        $db->beginTransaction();
        
        // Borrar todos los registros (en orden por dependencias)
        $db->exec("TRUNCATE TABLE topup_requests CASCADE");
        $db->exec("TRUNCATE TABLE keys CASCADE");
        $db->exec("TRUNCATE TABLE productos RESTART IDENTITY CASCADE");
        $db->exec("TRUNCATE TABLE payment_methods RESTART IDENTITY CASCADE");
        $db->exec("TRUNCATE TABLE usuarios RESTART IDENTITY CASCADE");
        
        $db->commit();
        header('Location: dashboard.php?success=Base de datos limpiada exitosamente');
        exit;
    } catch (PDOException $e) {
        if ($db->inTransaction()) $db->rollBack();
        header('Location: dashboard.php?error=Error al limpiar: ' . $e->getMessage());
        exit;
    }
}

// Obtener estadísticas
$stats = [
    'total_usuarios' => $db->query("SELECT COUNT(*) FROM usuarios")->fetchColumn(),
    'total_productos' => $db->query("SELECT COUNT(*) FROM productos")->fetchColumn(),
    'keys_disponibles' => $db->query("SELECT COUNT(*) FROM keys WHERE estado = 'available'")->fetchColumn(),
    'recargas_pendientes' => $db->query("SELECT COUNT(*) FROM topup_requests WHERE status = 'pending'")->fetchColumn(),
    'balance_total' => $db->query("SELECT COALESCE(SUM(saldo), 0) FROM usuarios")->fetchColumn()
];

// Últimas recargas
$stmt = $db->query("SELECT tr.*, u.username FROM topup_requests tr LEFT JOIN usuarios u ON tr.usuario_id = u.id ORDER BY tr.id DESC LIMIT 5");
$ultimas_recargas = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Panel Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: #fff;
            line-height: 1.6;
        }
        
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100vh;
            background: #12121a;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: #000;
        }
        
        .logo-text {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .nav-menu {
            list-style: none;
            padding: 16px 12px;
            flex: 1;
        }
        
        .nav-item {
            margin-bottom: 4px;
        }
        
        .nav-link {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: #a0a0b0;
            text-decoration: none;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            background: #252530;
            color: #fff;
        }
        
        .nav-link.active {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 204, 106, 0.1) 100%);
            color: #00ff88;
            border: 1px solid rgba(0, 255, 136, 0.2);
        }
        
        .badge {
            margin-left: auto;
            background: #ff4757;
            color: white;
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }
        
        .sidebar-footer {
            padding: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .admin-info {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: #252530;
            border-radius: 12px;
            margin-bottom: 12px;
            font-size: 0.9rem;
            color: #a0a0b0;
        }
        
        .logout-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px;
            color: #ff4757;
            text-decoration: none;
            border-radius: 12px;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .logout-btn:hover {
            background: rgba(255, 71, 87, 0.1);
        }
        
        .main-content {
            margin-left: 260px;
            padding: 32px;
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }
        
        .page-title {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .page-subtitle {
            color: #a0a0b0;
            margin-top: 4px;
        }
        
        .admin-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            background: #1a1a24;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 50px;
            font-size: 0.85rem;
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }
        
        .card {
            background: #1a1a24;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            display: block;
            color: inherit;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        }
        
        .card-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            margin-bottom: 16px;
        }
        
        .card h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .card p {
            font-size: 0.9rem;
            color: #a0a0b0;
            line-height: 1.5;
            margin-bottom: 16px;
        }
        
        .card-badge {
            display: inline-block;
            padding: 4px 12px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .card-red .card-icon { background: linear-gradient(135deg, #ff4757 0%, #cc3645 100%); color: white; }
        .card-green .card-icon { background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); color: #000; }
        .card-cyan .card-icon { background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); color: white; }
        .card-teal .card-icon { background: linear-gradient(135deg, #00b894 0%, #00897b 100%); color: white; }
        .card-pink .card-icon { background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); color: white; }
        .card-blue .card-icon { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; }
        
        .table-container {
            background: #1a1a24;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            overflow: hidden;
            margin-top: 40px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        th {
            background: #252530;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #a0a0b0;
        }
        
        tr:hover td {
            background: #252530;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: capitalize;
        }
        
        .status-pending { background: rgba(253, 203, 110, 0.15); color: #fdcb6e; }
        .status-approved { background: rgba(0, 255, 136, 0.15); color: #00ff88; }
        .status-rejected { background: rgba(255, 71, 87, 0.15); color: #ff4757; }
        
        .section-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title i {
            color: #00ff88;
        }
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
            <li class="nav-item">
                <a href="dashboard.php" class="nav-link active">
                    <i class="fas fa-home"></i>
                    <span>Dashboard</span>
                </a>
            </li>
            <li class="nav-item">
                <a href="recargas.php" class="nav-link">
                    <i class="fas fa-wallet"></i>
                    <span>Gestión de Recargas</span>
                    <?php if ($stats['recargas_pendientes'] > 0): ?>
                    <span class="badge"><?= $stats['recargas_pendientes'] ?></span>
                    <?php endif; ?>
                </a>
            </li>
            <li class="nav-item">
                <a href="productos.php" class="nav-link">
                    <i class="fas fa-key"></i>
                    <span>Portal de Licencias</span>
                </a>
            </li>
            <li class="nav-item">
                <a href="usuarios.php" class="nav-link">
                    <i class="fas fa-users"></i>
                    <span>Usuarios</span>
                </a>
            </li>
            <li class="nav-item">
                <a href="metodos_pago.php" class="nav-link">
                    <i class="fas fa-credit-card"></i>
                    <span>Métodos de Pago</span>
                </a>
            </li>
            <li class="nav-item">
                <a href="anuncios.php" class="nav-link">
                    <i class="fas fa-bullhorn"></i>
                    <span>Anuncios</span>
                </a>
            </li>
        </ul>
        
        <div class="sidebar-footer">
            <div class="admin-info">
                <i class="fas fa-user-shield"></i>
                <span><?= e($_SESSION['admin_user']) ?></span>
            </div>
            <a href="logout.php" class="logout-btn">
                <i class="fas fa-sign-out-alt"></i>
                Cerrar Sesión
            </a>
        </div>
    </nav>
    
    <main class="main-content">
        <div class="page-header">
            <div>
                <h1 class="page-title">Panel de Administración</h1>
                <p class="page-subtitle">Gestiona tu tienda desde un solo lugar</p>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <button onclick="confirmarLimpiar()" style="padding: 10px 20px; background: linear-gradient(135deg, #ff4757 0%, #cc3645 100%); color: white; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    <i class="fas fa-trash-alt"></i>
                    Limpiar Base de Datos
                </button>
                <div class="admin-badge">
                    <i class="fas fa-shield-alt"></i>
                    <span>Administrador: <?= e($_SESSION['admin_user']) ?></span>
                </div>
            </div>
        </div>
        
        <?php if ($success): ?>
        <div style="padding: 14px 18px; border-radius: 12px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.2); color: #00ff88;">
            <i class="fas fa-check-circle"></i>
            <?= e($success) ?>
        </div>
        <?php endif; ?>
        
        <?php if ($error): ?>
        <div style="padding: 14px 18px; border-radius: 12px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; background: rgba(255, 71, 87, 0.1); border: 1px solid rgba(255, 71, 87, 0.2); color: #ff4757;">
            <i class="fas fa-exclamation-circle"></i>
            <?= e($error) ?>
        </div>
        <?php endif; ?>
        
        <div class="cards-grid">
            <a href="recargas.php" class="card card-red">
                <div class="card-icon">
                    <i class="fas fa-bell"></i>
                </div>
                <h3>Central de Pedidos</h3>
                <p>Vista rápida de TODOS los pedidos nuevos: recargas, doxeos, retiros, redes. ¡Ahorra tiempo!</p>
            </a>
            
            <a href="recargas.php" class="card card-green">
                <div class="card-icon">
                    <i class="fas fa-wallet"></i>
                </div>
                <h3>Gestión de Recargas</h3>
                <p>Aprueba o rechaza solicitudes de recarga de saldo de los clientes.</p>
                <?php if ($stats['recargas_pendientes'] > 0): ?>
                <div class="card-badge"><?= $stats['recargas_pendientes'] ?> pendientes</div>
                <?php endif; ?>
            </a>
            
            <div class="card card-cyan">
                <div class="card-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <h3>Finanzas / Ganancias</h3>
                <p>Revisa ingresos por recargas y pedidos, y los productos/servicios más vendidos.</p>
                <div class="card-badge"><?= formatMoney($stats['balance_total']) ?> Balance Total</div>
            </div>
            
            <a href="usuarios.php" class="card card-teal">
                <div class="card-icon">
                    <i class="fas fa-users"></i>
                </div>
                <h3>Usuarios</h3>
                <p>Buscar usuarios, ver métricas y ajustar saldo (solo superadmin)</p>
                <div class="card-badge"><?= $stats['total_usuarios'] ?> registrados</div>
            </a>
            
            <a href="productos.php" class="card card-pink">
                <div class="card-icon">
                    <i class="fas fa-key"></i>
                </div>
                <h3>Portal de Licencias</h3>
                <p>Crea usuarios para generadores Drip, BR Mods y Sticks.</p>
                <div class="card-badge"><?= $stats['keys_disponibles'] ?> keys disponibles</div>
            </a>
            
            <a href="metodos_pago.php" class="card card-blue">
                <div class="card-icon">
                    <i class="fas fa-credit-card"></i>
                </div>
                <h3>Métodos de Pago</h3>
                <p>Crea, edita y elimina países, tasas y métodos de pago para recargas.</p>
            </a>

            <a href="anuncios.php" class="card card-red">
                <div class="card-icon">
                    <i class="fas fa-bullhorn"></i>
                </div>
                <h3>Anuncios</h3>
                <p>Envía anuncios masivos a los usuarios vinculados en Telegram.</p>
            </a>
        </div>
        
        <h2 class="section-title">
            <i class="fas fa-clock"></i>
            Últimas Recargas
        </h2>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Usuario</th>
                        <th>Monto</th>
                        <th>Estado</th>
                        <th>Fecha</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (count($ultimas_recargas) > 0): ?>
                        <?php foreach ($ultimas_recargas as $recarga): ?>
                        <tr>
                            <td>#<?= $recarga['id'] ?></td>
                            <td><?= e($recarga['username'] ?? 'N/A') ?></td>
                            <td><?= formatMoney($recarga['monto']) ?></td>
                            <td>
                                <span class="status-badge status-<?= $recarga['status'] ?>">
                                    <?= e($recarga['status']) ?>
                                </span>
                            </td>
                            <td><?= formatDate($recarga['fecha_creacion']) ?></td>
                        </tr>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <tr>
                            <td colspan="5" style="text-align: center; color: #606070;">No hay recargas recientes</td>
                        </tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </main>
    
    <!-- Formulario oculto para limpiar DB -->
    <form id="limpiarForm" method="POST" style="display: none;">
        <input type="hidden" name="action" value="limpiar_db">
    </form>
    
    <script>
        function confirmarLimpiar() {
            if (confirm('⚠️ ADVERTENCIA: Esto borrará TODOS los datos de la base de datos:\n\n- Todos los usuarios\n- Todos los productos\n- Todas las keys\n- Todos los métodos de pago\n- Todas las recargas\n\n¿Estás seguro de continuar?')) {
                if (confirm('Esta acción NO se puede deshacer. ¿Confirmas que deseas borrar TODO?')) {
                    document.getElementById('limpiarForm').submit();
                }
            }
        }
    </script>
</body>
</html>
