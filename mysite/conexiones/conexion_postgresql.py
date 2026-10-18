import psycopg2
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_PATH)


class ConexionPostgresql:

    def __init__(self):
        # Credenciales desde variables de entorno (con valores por defecto opcionales)
        self.HOST = os.environ.get("HOST", "localhost")
        self.DATABASE_NAME = os.environ.get("DATABASE_NAME", "centro_idiomas")
        self.USER = os.environ.get("PG_USER", "postgres")
        self.PASSWORD = os.environ.get("PG_PASSWORD", "postgres@")
        self.PORT = os.environ.get("PORT", 5432)

        self.CNX = None  # Gestionar la conexión
        self.CURSOR = None  # Gestionar las consultas

    def crear_conexion(self):
        """Crea la conexión a la base de datos PostgreSQL"""
        try:
            self.CNX = psycopg2.connect(
                host=self.HOST,
                database=self.DATABASE_NAME,
                user=self.USER,
                password=self.PASSWORD,
                port=self.PORT
            )
            self.CURSOR = self.CNX.cursor()
            print(f"Conectado al servidor PostgreSQL: {self.HOST}")
            return self.CNX
        except Exception as e:
            print(f"Error al conectarse al servidor {self.HOST} de base de datos")
            print(e)
            self.CNX = None
            self.CURSOR = None
            return None

    def ejecutar_consulta(self, sql, parametros=None):
        """Método para realizar consultas a la base de datos y retornar diccionarios"""
        try:
            # Normalizar parámetros a minúsculas por si se envía {"Limite": 10}
            if isinstance(parametros, dict):
                parametros = {k.lower(): v for k, v in parametros.items()}

            if self.CNX is None or self.CNX.closed != 0:
                if self.crear_conexion() is None:
                    return {
                        "estado": False,
                        "tipo": "ConexionError",
                        "mensaje": "No fue posible conectarse a la base de datos",
                    }

            if parametros:
                self.CURSOR.execute(sql, parametros)
            else:
                self.CURSOR.execute(sql)

            tipo = sql.strip().split()[0].upper()

            # Consultas de Lectura (SELECT)
            if tipo == "SELECT":
                columnas = [columna[0] for columna in self.CURSOR.description]
                registros = self.CURSOR.fetchall()

                resultados = []
                for registro in registros:
                    fila = {}
                    for i, valor in enumerate(registro):
                        fila[columnas[i]] = valor
                    resultados.append(fila)

                # RETORNAR DICCIONARIO DIRECTAMENTE
                return {
                    "estado": True,
                    "tipo": "SELECT",
                    "registros": resultados,
                }

            # Consultas de Escritura
            elif tipo in ("INSERT", "UPDATE", "DELETE"):
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return {
                    "estado": True,
                    "tipo": tipo,
                    "mensaje": f"Operación {tipo} ejecutada correctamente",
                    "filas_afectadas": filas,
                }

            else:
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                return {
                    "estado": True,
                    "tipo": tipo,
                    "mensaje": "Consulta ejecutada correctamente",
                    "filas_afectadas": filas,
                }

        except psycopg2.IntegrityError as e:
            if self.CNX:
                self.CNX.rollback()
            return {
                "estado": False,
                "tipo": "IntegrityError",
                "mensaje": "Violación de integridad",
                "error": str(e),
            }

        except psycopg2.ProgrammingError as e:
            if self.CNX:
                self.CNX.rollback()
            return {
                "estado": False,
                "tipo": "ProgrammingError",
                "mensaje": "Error en la consulta SQL",
                "error": str(e),
            }

        except psycopg2.OperationalError as e:
            if self.CNX:
                try:
                    self.CNX.rollback()
                except Exception:
                    pass
            self.CNX = None
            self.CURSOR = None
            return {
                "estado": False,
                "tipo": "OperationalError",
                "mensaje": "Error de conexión",
                "error": str(e),
            }

        except Exception as e:
            if self.CNX:
                try:
                    self.CNX.rollback()
                except Exception:
                    pass
            return {
                "estado": False,
                "tipo": "Error",
                "mensaje": "Error inesperado",
                "error": str(e),
            }
    def cerrar_conexion(self):
        """Método para cerrar la conexión a la base de datos"""
        try:
            if self.CURSOR:
                self.CURSOR.close()
                self.CURSOR = None
            if self.CNX and self.CNX.closed == 0:
                self.CNX.close()
                self.CNX = None
            print(f"Se ha cerrado la conexión con el servidor: {self.HOST}")
            return True
        except Exception as e:
            print("Error al desconectarse de la base de datos")
            print(e)
            return False


if __name__ == '__main__':
    cnn = ConexionPostgresql()
    if cnn.crear_conexion():
        sql = """
        SELECT c.id_curso, i.nombre AS idioma, TRIM(n.equivalencia_mcer) AS nivel, c.horas_totales, c.costo
        FROM cursos c
        INNER JOIN idiomas i ON c.id_idioma = i.id_idioma
        INNER JOIN niveles n ON c.id_nivel = n.id_nivel
        ORDER BY c.id_curso
        """
        print(json.dumps(cnn.ejecutar_consulta(sql), indent=2, ensure_ascii=False, default=str))
        cnn.cerrar_conexion()