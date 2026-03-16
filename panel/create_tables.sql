-- Script SQL para crear las tablas del panel Torres Shop
-- Ejecutar en PostgreSQL (Railway)

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    login_key VARCHAR(255) NOT NULL,
    telegram_id BIGINT UNIQUE,
    saldo DECIMAL(10, 2) DEFAULT 0.00,
    es_admin BOOLEAN DEFAULT FALSE,
    idioma VARCHAR(5) DEFAULT 'es',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Para bases ya creadas anteriormente
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS idioma VARCHAR(5) DEFAULT 'es';

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    categoria VARCHAR(100),
    precio DECIMAL(10, 2) NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de keys/licencias
CREATE TABLE IF NOT EXISTS keys (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
    licencia VARCHAR(500) UNIQUE NOT NULL,
    estado VARCHAR(20) DEFAULT 'available',
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_compra TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de métodos de pago
CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    instrucciones TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de solicitudes de recarga
CREATE TABLE IF NOT EXISTS topup_requests (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    metodo_pago_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL,
    monto DECIMAL(10, 2) NOT NULL,
    referencia VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion TIMESTAMP
);

-- Crear índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_keys_producto ON keys(producto_id);
CREATE INDEX IF NOT EXISTS idx_keys_estado ON keys(estado);
CREATE INDEX IF NOT EXISTS idx_topup_status ON topup_requests(status);
CREATE INDEX IF NOT EXISTS idx_topup_usuario ON topup_requests(usuario_id);

-- Mensaje de confirmación
SELECT 'Tablas creadas exitosamente' AS resultado;
