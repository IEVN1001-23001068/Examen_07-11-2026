# ==========================================================
# CONFIGURACION DE LA APLICACION Y MySQL
# ==========================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Posibles archivos de variables de entorno.
# Se soporta .env (si es archivo) y .env.local (util cuando .env es un entorno virtual).
ENV_CANDIDATES = [
    BASE_DIR / '.env',
    BASE_DIR / '.env.local',
    BASE_DIR / 'config.env',
]


def _cargar_env():
    """Carga variables de entorno desde el primer archivo legible encontrado."""
    for env_path in ENV_CANDIDATES:
        if not env_path.is_file():
            continue

        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            return
        except ImportError:
            pass

        try:
            for linea in env_path.read_text(encoding='utf-8').splitlines():
                linea = linea.strip()
                if not linea or linea.startswith('#') or '=' not in linea:
                    continue

                clave, valor = linea.split('=', 1)
                clave = clave.strip()
                valor = valor.strip()

                if (valor.startswith('"') and valor.endswith('"')) or \
                   (valor.startswith("'") and valor.endswith("'")):
                    valor = valor[1:-1]

                os.environ.setdefault(clave, valor)
            return
        except (OSError, PermissionError):
            continue


_cargar_env()


class DevelopmentConfig:
    DEBUG = True

    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'Danonino')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Di203020137-6')
    MYSQL_DB = os.getenv('MYSQL_DB', 'pizzeriaalfredo')
    MYSQL_CURSORCLASS = 'Cursor'


config = {
    'development': DevelopmentConfig
}
