import os
import logging
import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, BigInteger, ForeignKey, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
from dotenv import load_dotenv 

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO)

# --- Definición de la Base ---
Base = declarative_base()

# --- Modelos de Datos ---
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True) 
    username = Column(String(50), unique=True, nullable=False)
    login_key = Column(String(100), nullable=False) 
    saldo = Column(Float, default=0.00)
    es_admin = Column(Boolean, default=False)
    idioma = Column(String(5), default='es')
    fecha_registro = Column(DateTime, default=datetime.now)

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    precio = Column(Float, nullable=False)
    descripcion = Column(String(255)) 
    fecha_creacion = Column(DateTime, default=datetime.now)
    keys = relationship("Key", back_populates="producto")

class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    instrucciones = Column(String(1000), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)

class TopUpRequest(Base):
    __tablename__ = 'topup_requests'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    metodo_pago_id = Column(Integer, ForeignKey('payment_methods.id'), nullable=True)
    monto = Column(Float, nullable=False)
    referencia = Column(String(255), nullable=True)
    status = Column(String(20), default='pending')
    nota_admin = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_resolucion = Column(DateTime, nullable=True)
    admin_telegram_id = Column(BigInteger, nullable=True)

    usuario = relationship("Usuario")
    metodo_pago = relationship("PaymentMethod")

class Key(Base):
    __tablename__ = 'keys'
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    licencia = Column(String(255), unique=True, nullable=False)
    estado = Column(String(20), default='available') 
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    fecha_compra = Column(DateTime, nullable=True)
    producto = relationship("Producto", back_populates="keys")


# --- Conexión y Sesión (Lee DATABASE_URL de ENV) ---
load_dotenv() 
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///socios_bot.db') 
ENGINE = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

def get_session():
    """Retorna una nueva sesión de SQLAlchemy."""
    return SessionLocal()

def inicializar_db(engine=ENGINE): 
    """Crea las tablas, y el usuario administrador si no existen."""
    Base.metadata.create_all(bind=engine) 

    # Migraciones ligeras para esquemas existentes
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS idioma VARCHAR(5) DEFAULT 'es'"))
            conn.execute(text("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS nota_admin VARCHAR(255)"))
            conn.execute(text("ALTER TABLE topup_requests ADD COLUMN IF NOT EXISTS admin_telegram_id BIGINT"))
            conn.execute(text("ALTER TABLE keys ADD COLUMN IF NOT EXISTS usuario_id INTEGER"))
            conn.execute(text("ALTER TABLE keys ADD COLUMN IF NOT EXISTS fecha_compra TIMESTAMP"))
    except Exception as e:
        logging.warning(f"No se pudieron aplicar migraciones automáticas: {e}")

    Session = sessionmaker(bind=engine)
    with Session() as session:
        if session.query(Usuario).filter(Usuario.es_admin == True).count() == 0:
            logging.info("Insertando USUARIO ADMINISTRADOR INICIAL: admin/adminpass")
            admin_user = Usuario(username='admin', login_key='adminpass', saldo=1000.00, es_admin=True)
            session.add(admin_user)
            session.commit()
            print("Base de datos inicializada con usuario administrador.")
        else:
             print("Base de datos verificada. Usuario administrador existente.")


if __name__ == '__main__':
    # Este bloque se ejecuta cuando el comando de inicio en Railway llama a este archivo.
    print(f"Conectando a Base de Datos con URL: {DATABASE_URL}")
    try:
        inicializar_db(ENGINE) 
        print("¡Proceso de creación de tablas finalizado con éxito!")
    except Exception as e:
        print(f"\n--- ERROR CRÍTICO DE CONEXIÓN EN DB_MODELS.PY ---\nDetalle: {e}")
        sys.exit(1)