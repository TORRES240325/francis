<?php
require_once 'config.php';

// Si ya está logueado, redirigir al dashboard
if (isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true) {
    header('Location: dashboard.php');
    exit;
}

$error = '';

// Procesar login
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($username === ADMIN_USERNAME && $password === ADMIN_PASSWORD) {
        $_SESSION['admin_logged_in'] = true;
        $_SESSION['admin_user'] = $username;
        header('Location: dashboard.php');
        exit;
    } else {
        $error = 'Credenciales inválidas';
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Panel Admin Torres Shop</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-container {
            background: rgba(20, 20, 30, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .logo-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 700;
            color: #000;
            margin: 0 auto 20px;
        }
        
        h1 {
            color: #00ff88;
            font-size: 1.8rem;
            text-align: center;
            margin-bottom: 8px;
        }
        
        .subtitle {
            color: #888;
            font-size: 0.9rem;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .alert {
            padding: 14px 18px;
            border-radius: 12px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 71, 87, 0.1);
            border: 1px solid rgba(255, 71, 87, 0.3);
            color: #ff4757;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #aaa;
            font-size: 0.85rem;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        input:focus {
            outline: none;
            border-color: #00ff88;
            box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
            border: none;
            border-radius: 12px;
            color: #000;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
        }
        
        .footer {
            text-align: center;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #666;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-icon">TX</div>
        <h1>Panel de Administración</h1>
        <p class="subtitle">Gestiona tu tienda desde un solo lugar</p>
        
        <?php if ($error): ?>
        <div class="alert">
            <i class="fas fa-exclamation-circle"></i>
            <?= e($error) ?>
        </div>
        <?php endif; ?>
        
        <form method="POST">
            <div class="form-group">
                <label>
                    <i class="fas fa-user"></i>
                    Usuario
                </label>
                <input type="text" name="username" required placeholder="Ingresa tu usuario" autocomplete="username">
            </div>
            
            <div class="form-group">
                <label>
                    <i class="fas fa-lock"></i>
                    Contraseña
                </label>
                <input type="password" name="password" required placeholder="Ingresa tu contraseña" autocomplete="current-password">
            </div>
            
            <button type="submit">
                <i class="fas fa-sign-in-alt"></i>
                Iniciar Sesión
            </button>
        </form>
        
        <div class="footer">
            <i class="fas fa-shield-alt"></i>
            Acceso solo para administradores
        </div>
    </div>
</body>
</html>
