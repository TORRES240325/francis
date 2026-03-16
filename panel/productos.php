<?php
require_once 'config.php';
requireLogin();

$db = getDB();
$success = $_GET['success'] ?? '';
$error = $_GET['error'] ?? '';

// Procesar acciones
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        if (isset($_POST['action'])) {
            if ($_POST['action'] === 'crear_producto') {
                $stmt = $db->prepare("INSERT INTO productos (nombre, categoria, precio, descripcion) VALUES (?, ?, ?, ?)");
                $stmt->execute([
                    $_POST['nombre'],
                    $_POST['categoria'],
                    floatval($_POST['precio']),
                    $_POST['descripcion'] ?? ''
                ]);
                header('Location: productos.php?success=Producto creado');
                exit;
            } elseif ($_POST['action'] === 'agregar_keys') {
                $product_id = intval($_POST['product_id']);
                $keys_text = $_POST['keys_text'];
                $keys_list = array_filter(array_map('trim', explode("\n", $keys_text)));
                
                $agregadas = 0;
                foreach ($keys_list as $key_str) {
                    $check = $db->prepare("SELECT id FROM keys WHERE licencia = ?");
                    $check->execute([$key_str]);
                    if (!$check->fetch()) {
                        $stmt = $db->prepare("INSERT INTO keys (producto_id, licencia, estado) VALUES (?, ?, 'available')");
                        $stmt->execute([$product_id, $key_str]);
                        $agregadas++;
                    }
                }
                header("Location: productos.php?success=$agregadas keys agregadas");
                exit;
            }
        }
    } catch (PDOException $e) {
        $error = 'Error: ' . $e->getMessage();
    }
}

// Obtener productos con stock
$productos = $db->query("SELECT p.*, 
    (SELECT COUNT(*) FROM keys k WHERE k.producto_id = p.id AND k.estado = 'available') as stock 
    FROM productos p ORDER BY p.id DESC")->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal de Licencias - Panel Admin</title>
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
        
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
        .product-card { background: #1a1a24; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 24px; display: flex; flex-direction: column; }
        .product-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .product-icon { width: 48px; height: 48px; background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; color: white; }
        .product-info { flex: 1; }
        .product-info h3 { font-size: 1.1rem; margin-bottom: 4px; }
        .category-badge { display: inline-block; padding: 2px 10px; background: rgba(116, 185, 255, 0.15); border-radius: 20px; font-size: 0.75rem; color: #74b9ff; }
        .product-price { font-size: 1.3rem; font-weight: 700; color: #00ff88; }
        .product-desc { color: #888; font-size: 0.9rem; margin-bottom: 16px; min-height: 40px; }
        .stock-bar { margin-bottom: 16px; }
        .stock-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .stock-label { font-size: 0.85rem; color: #888; }
        .stock-number { font-weight: 600; color: #fff; }
        .stock-progress { height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #00ff88 0%, #00cc6a 100%); border-radius: 3px; transition: width 0.3s ease; }
        .product-actions { display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
        .product-id { color: #666; font-size: 0.8rem; }
        
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
        textarea.form-control { min-height: 100px; resize: vertical; font-family: 'Inter', sans-serif; }
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
            <li class="nav-item"><a href="productos.php" class="nav-link active"><i class="fas fa-key"></i><span>Licencias</span></a></li>
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
                <h1 class="page-title">Portal de Licencias</h1>
                <p class="page-subtitle">Crea productos y gestiona stock de keys</p>
            </div>
            <button class="btn btn-primary" onclick="openModal('createProductModal')">
                <i class="fas fa-plus"></i> Crear Producto
            </button>
        </div>
        
        <?php if ($success): ?>
        <div class="alert alert-success"><i class="fas fa-check-circle"></i><?= e($success) ?></div>
        <?php endif; ?>
        
        <?php if ($error): ?>
        <div class="alert alert-error"><i class="fas fa-exclamation-circle"></i><?= e($error) ?></div>
        <?php endif; ?>
        
        <div class="cards-grid">
            <?php foreach ($productos as $p): ?>
            <div class="product-card">
                <div class="product-header">
                    <div class="product-icon"><i class="fas fa-key"></i></div>
                    <div class="product-info">
                        <h3><?= e($p['nombre']) ?></h3>
                        <span class="category-badge"><?= e($p['categoria']) ?></span>
                    </div>
                    <div class="product-price"><?= formatMoney($p['precio']) ?></div>
                </div>
                
                <p class="product-desc"><?= e($p['descripcion'] ?: 'Sin descripción') ?></p>
                
                <div class="stock-bar">
                    <div class="stock-info">
                        <span class="stock-label">Stock disponible</span>
                        <span class="stock-number"><?= $p['stock'] ?></span>
                    </div>
                    <div class="stock-progress">
                        <div class="progress-fill" style="width: <?= min($p['stock'] / 50 * 100, 100) ?>%;"></div>
                    </div>
                </div>
                
                <div class="product-actions">
                    <button class="btn btn-sm btn-primary" onclick="openAddKeysModal(<?= $p['id'] ?>, '<?= e($p['nombre']) ?>')">
                        <i class="fas fa-plus-circle"></i> Agregar Keys
                    </button>
                    <span class="product-id">ID: <?= $p['id'] ?></span>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </main>
    
    <!-- Modal Crear Producto -->
    <div id="createProductModal" class="modal-overlay">
        <div class="modal">
            <div class="modal-header"><h2><i class="fas fa-plus"></i> Crear Nuevo Producto</h2></div>
            <form method="POST">
                <input type="hidden" name="action" value="crear_producto">
                <div class="modal-body">
                    <div class="form-group">
                        <label>Nombre del Producto</label>
                        <input type="text" name="nombre" class="form-control" required placeholder="ej: Drip Generator">
                    </div>
                    <div class="form-group">
                        <label>Categoría</label>
                        <input type="text" name="categoria" class="form-control" required placeholder="ej: Generadores, Mods, etc.">
                    </div>
                    <div class="form-group">
                        <label>Precio ($)</label>
                        <input type="number" step="0.01" name="precio" class="form-control" required placeholder="10.00">
                    </div>
                    <div class="form-group">
                        <label>Descripción (opcional)</label>
                        <textarea name="descripcion" class="form-control" placeholder="Descripción del producto..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('createProductModal')">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Crear Producto</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Modal Agregar Keys -->
    <div id="addKeysModal" class="modal-overlay">
        <div class="modal">
            <div class="modal-header"><h2><i class="fas fa-key"></i> Agregar Keys</h2></div>
            <form method="POST">
                <input type="hidden" name="action" value="agregar_keys">
                <input type="hidden" name="product_id" id="keysProductId">
                <div class="modal-body">
                    <p style="margin-bottom: 20px;">Producto: <strong id="keysProductName"></strong></p>
                    <div class="form-group">
                        <label>Keys / Licencias (una por línea)</label>
                        <textarea name="keys_text" class="form-control" rows="10" required placeholder="XXXX-XXXX-XXXX-XXXX
YYYY-YYYY-YYYY-YYYY
ZZZZ-ZZZZ-ZZZZ-ZZZZ"></textarea>
                    </div>
                    <p style="color: #666; font-size: 0.85rem; margin-top: 10px;">
                        <i class="fas fa-info-circle"></i> Las keys duplicadas serán ignoradas automáticamente.
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('addKeysModal')">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Agregar Keys</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function openModal(id) { document.getElementById(id).classList.add('active'); }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        function openAddKeysModal(productId, productName) {
            document.getElementById('keysProductId').value = productId;
            document.getElementById('keysProductName').textContent = productName;
            openModal('addKeysModal');
        }
        window.onclick = function(event) {
            if (event.target.classList.contains('modal-overlay')) {
                event.target.classList.remove('active');
            }
        }
    </script>
</body>
</html>
