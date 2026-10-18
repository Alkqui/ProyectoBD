import mssql_python
import json
import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Conexion_sql_server:
    def __init__(self):
        load_dotenv(ENV_PATH)
        self.SERVER = os.environ.get("SERVER")
        self.DATABASE_NAME = os.environ.get("DATABASE_NAME")
        self.USER = os.environ.get("DB_USER")          # renombrado (evita choque con USER de Linux)
        self.PASSWORD = os.environ.get("DB_PASSWORD")
        self.CNX = None      # Gestiona la conexion
        self.CURSOR = None   # Gestiona las consultas

    # ---------- Conexion ----------
    def crear_conexion(self):
        try:
            cadena_conexion = (
                f"Server={self.SERVER};"
                f"Database={self.DATABASE_NAME};"
                f"UID={self.USER};"
                f"PWD={self.PASSWORD};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
            )
            self.CNX = mssql_python.connect(cadena_conexion)
            self.CURSOR = self.CNX.cursor()
            print(f"Conectado al servidor {self.SERVER}")
            return self.CNX
        except mssql_python.Error as e:
            print(f"Conexion fallida con {self.SERVER} / {self.DATABASE_NAME}")
            print(e)
            self.CNX = None
            self.CURSOR = None
            return None

    def cerrar_conexion(self):
        try:
            if self.CURSOR:
                self.CURSOR.close()
                self.CURSOR = None
            if self.CNX:
                self.CNX.close()
                self.CNX = None
            print(f"Se ha cerrado la conexion con {self.SERVER} de forma exitosa")
        except mssql_python.Error as e:
            print(f"Error al cerrar la conexion con {self.SERVER}")
            print(e)
            return None

    # ---------- Utilidades ----------
    def _error(self, tipo, e):
        """Deshace la transaccion y devuelve el error como JSON."""
        try:
            if self.CNX:
                self.CNX.rollback()
        except Exception:
            pass
        return json.dumps(
            {"estado": False, "tipo": tipo, "error": str(e)},
            ensure_ascii=False,
        )

    # ---------- Consultas ----------
    def ejecutar_consulta(self, sql, parametros=None):
        if not self.CURSOR:
            return json.dumps(
                {"estado": False, "mensaje": "No hay conexion establecida"},
                ensure_ascii=False,
            )

        try:
            if parametros:
                self.CURSOR.execute(sql, parametros)
            else:
                self.CURSOR.execute(sql)

            tipo = sql.split()[0].upper()

            if tipo == "SELECT":
                columnas = [c[0] for c in self.CURSOR.description]
                registros = self.CURSOR.fetchall()
                resultados = [dict(zip(columnas, r)) for r in registros]
                return json.dumps(
                    {"estado": True, "tipo": "SELECT",
                     "total": len(resultados), "registros": resultados},
                    default=str, ensure_ascii=False,
                )

            elif tipo in ("INSERT", "UPDATE", "DELETE"):
                filas = self.CURSOR.rowcount
                self.CNX.commit()
                mensajes = {
                    "INSERT": "Registro insertado",
                    "UPDATE": "Registro actualizado",
                    "DELETE": "Registro eliminado",
                }
                return json.dumps(
                    {"estado": True, "tipo": tipo,
                     "mensaje": mensajes[tipo], "filas_afectadas": filas},
                    ensure_ascii=False,
                )

            else:
                # CREATE, DROP, ALTER, etc.
                self.CNX.commit()
                return json.dumps(
                    {"estado": True, "tipo": tipo,
                     "mensaje": f"Sentencia {tipo} ejecutada"},
                    ensure_ascii=False,
                )

        except mssql_python.IntegrityError as e:
            # llave duplicada, FK, NOT NULL, etc.
            return self._error("INTEGRITY ERROR", e)
        except mssql_python.ProgrammingError as e:
            # SQL mal escrito, tabla o columna inexistente
            return self._error("PROGRAMMING ERROR", e)
        except mssql_python.OperationalError as e:
            # conexion perdida, timeout, etc.
            return self._error("OPERATIONAL ERROR", e)
        except mssql_python.Error as e:
            return self._error("DATABASE ERROR", e)
        except Exception as e:
            return self._error("ERROR INESPERADO", e)


def mostrar(titulo, resultado_json):
    print(f"\n--- {titulo} ---")
    data = json.loads(resultado_json)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


if __name__ == "__main__":
    cnn = Conexion_sql_server()

    if cnn.crear_conexion():
        # Limpieza por si una corrida anterior fallo a la mitad
        cnn.ejecutar_consulta(
            "IF OBJECT_ID('PruebaClientes') IS NOT NULL DROP TABLE PruebaClientes"
        )

        # 1. CREATE
        mostrar("CREATE TABLE", cnn.ejecutar_consulta("""
            CREATE TABLE PruebaClientes (
                Id INT PRIMARY KEY,
                Nombre NVARCHAR(50) NOT NULL,
                Ciudad NVARCHAR(50)
            )
        """))

        # 2. INSERT (con parametros)
        mostrar("INSERT 1", cnn.ejecutar_consulta(
            "INSERT INTO PruebaClientes (Id, Nombre, Ciudad) VALUES (?, ?, ?)",
            (1, "Ana", "Sahuayo")))
        mostrar("INSERT 2", cnn.ejecutar_consulta(
            "INSERT INTO PruebaClientes (Id, Nombre, Ciudad) VALUES (?, ?, ?)",
            (2, "Luis", "Jiquilpan")))

        # 3. SELECT simple
        mostrar("SELECT todos", cnn.ejecutar_consulta(
            "SELECT * FROM PruebaClientes"))

        # 4. SELECT con parametro
        mostrar("SELECT filtrado", cnn.ejecutar_consulta(
            "SELECT * FROM PruebaClientes WHERE Ciudad = ?", ("Sahuayo",)))

        # 5. UPDATE
        mostrar("UPDATE", cnn.ejecutar_consulta(
            "UPDATE PruebaClientes SET Ciudad = ? WHERE Id = ?", ("Zamora", 2)))

        # 6. DELETE
        mostrar("DELETE", cnn.ejecutar_consulta(
            "DELETE FROM PruebaClientes WHERE Id = ?", (1,)))


        cnn.ejecutar_consulta("DROP TABLE PruebaClientes")

    cnn.cerrar_conexion()