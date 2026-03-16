# 🚀 Panel Admin PHP - Torres Shop

Panel de administración en PHP puro con CSS embebido en cada archivo. Diseño dark theme con tarjetas.

## 📁 Archivos del Panel

```
panel/
├── config.php           # Configuración DB + sesiones
├── login.php           # Login con diseño dark
├── logout.php          # Cerrar sesión
├── dashboard.php       # Dashboard con tarjetas
├── usuarios.php        # Gestión de usuarios
├── productos.php       # Portal de licencias + stock
├── recargas.php        # Aprobar/rechazar recargas
└── metodos_pago.php    # CRUD métodos de pago
```

**Cada archivo PHP tiene su CSS embebido** (sin archivos `.css` externos).

## 🔧 Requisitos en tu VPS

- **PHP 8.0+** con extensiones:
  - `pdo_pgsql` (para conectar a PostgreSQL)
  - `session`
- **PostgreSQL** (Railway o local)
- **Nginx** o **Apache**

## 📍 Instalación en tu VPS

### 1. Subir archivos al VPS

Copia la carpeta `panel/` a tu servidor:

```bash
# En tu VPS
cd /var/www/torresshophacks.com/public
mkdir panel
```

Luego sube todos los archivos PHP a `/var/www/torresshophacks.com/public/panel/`

### 2. Configurar credenciales en `config.php`

Edita `config.php` líneas 10-15 y 18-19:

```php
// Configuración de Base de Datos (PostgreSQL en Railway)
define('DB_HOST', 'switchback.proxy.rlwy.net');
define('DB_PORT', '12748');
define('DB_NAME', 'railway');
define('DB_USER', 'postgres');
define('DB_PASS', 'vdXRWNDASnlinYyBUgypxIMNDixdymnW');

// Credenciales del panel admin
define('ADMIN_USERNAME', 'admin');
define('ADMIN_PASSWORD', 'CAMBIA_ESTO_POR_PASSWORD_SEGURO');
```

⚠️ **IMPORTANTE**: Cambia `ADMIN_PASSWORD` por una contraseña segura.

### 3. Verificar extensión PDO PostgreSQL en PHP

```bash
# Verificar si está instalada
php -m | grep pdo_pgsql

# Si no está, instalar (Ubuntu/Debian)
sudo apt install php-pgsql
sudo systemctl restart php8.1-fpm  # o tu versión de PHP
sudo systemctl restart nginx
```

### 4. Configurar permisos

```bash
cd /var/www/torresshophacks.com/public/panel
sudo chown -R www-data:www-data .
sudo chmod -R 755 .
```

### 5. Acceder al panel

Abre en tu navegador:

```
https://torresshophacks.com/panel/login.php
```

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: la que pusiste en `config.php`

## 🎯 Funcionalidades del Panel

### Dashboard
- Vista general con tarjetas
- Estadísticas en tiempo real
- Últimas recargas

### Usuarios
- Crear usuarios con saldo inicial
- Ajustar saldo (sumar/restar)
- Ver usuarios registrados

### Portal de Licencias (Productos)
- Crear productos por categoría
- Agregar keys en bulk (una por línea)
- Ver stock disponible en tiempo real

### Gestión de Recargas
- Ver recargas pendientes/aprobadas/rechazadas
- Aprobar recarga (suma saldo automáticamente)
- Rechazar recarga
- Filtros por estado

### Métodos de Pago
- Crear métodos (nombre + instrucciones)
- Activar/desactivar métodos
- Los usuarios ven solo los activos

## 🔒 Seguridad

1. **Cambia la contraseña** en `config.php`
2. **No subas `config.php` a Git** (añádelo a `.gitignore`)
3. Considera usar **HTTPS** (Certbot/Let's Encrypt)
4. Opcional: protege `/panel/` con **IP whitelist** en Nginx

## 🌐 Configuración Nginx (opcional)

Si quieres que `/panel` redirija automáticamente a `/panel/login.php`:

```nginx
location /panel {
    index login.php;
    try_files $uri $uri/ /panel/login.php?$query_string;
}

location ~ \.php$ {
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
}
```

Luego:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 🐛 Troubleshooting

### Error: "could not find driver"
Falta extensión PDO PostgreSQL:
```bash
sudo apt install php-pgsql
sudo systemctl restart php8.1-fpm nginx
```

### Error: "Connection refused"
Verifica que las credenciales de `config.php` sean correctas y que Railway permita conexiones desde tu IP.

### Página en blanco
Activa errores en `config.php` (línea 3):
```php
ini_set('display_errors', 1);
error_reporting(E_ALL);
```

## 📝 Notas

- **El bot de Telegram y el panel comparten la misma DB** (PostgreSQL en Railway)
- Cuando apruebes una recarga en el panel, el saldo se actualiza automáticamente
- Los usuarios pueden ver sus keys compradas en el bot de Telegram

## 🔄 Actualizar el panel

```bash
cd /var/www/torresshophacks.com/public/panel
# Sube los archivos nuevos
sudo chown -R www-data:www-data .
```

---

**Panel creado para Torres Shop Hacks**  
Diseño dark theme con CSS embebido en cada PHP
