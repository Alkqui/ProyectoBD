import json
import os

def clear():
    # Limpia la pantalla usando secuencias ANSI, perfecto para PyCharm y terminales
    print("\033[H\033[J", end="")

def print_table(rows, headers):
    if not rows:
        print("  (sin resultados)")
        return

    col_widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(r.get(h, ''))))

    line = "+" + "+".join("-" * (col_widths[h] + 2) for h in headers) + "+"
    print(line)
    header_row = "| " + " | ".join(str(h).ljust(col_widths[h]) for h in headers) + " |"
    print(header_row)
    print(line)
    for r in rows:
        row_str = "| " + " | ".join(str(r.get(h, '')).ljust(col_widths[h]) for h in headers) + " |"
        print(row_str)
    print(line)


class MenuCentroIdiomas:
    def __init__(self, db_conexion):
        self.db = db_conexion
        # Detectamos qué clase de conexión nos enviaron para adaptarnos a ella
        self.nombre_clase_db = type(self.db).__name__

    def _ejecutar(self, sql, parametros=None):
        """
        Método Adaptador: Recibe SQL estándar (con '?') y lo traduce automáticamente
        según el motor de base de datos (PostgreSQL o SQL Server).
        """
        if "Postgresql" in self.nombre_clase_db:
            sql = sql.replace("?", "%s")
        if hasattr(self.db, "ejecutar_consulta"):
            return self.db.ejecutar_consulta(sql, parametros)
        return self.db.ejecutar_consultas(sql, parametros)

    def mostrar_banner(self):
        print("=" * 70)
        print(" ██╗██████╗ ██╗ ██████╗ ███╗   ███╗ █████╗ ███████╗".center(70))
        print(" ██║██╔══██╗██║██╔═══██╗████╗ ████║██╔══██╗██╔════╝".center(70))
        print(" ██║██║  ██║██║██║   ██║██╔████╔██║███████║███████╗".center(70))
        print(" ██║██║  ██║██║██║   ██║██║╚██╔╝██║██╔══██║╚════██║".center(70))
        print(" ██║██████╔╝██║╚██████╔╝██║ ╚═╝ ██║██║  ██║███████║".center(70))
        print(" ╚═╝╚═════╝ ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝".center(70))
        print("=" * 70)
        print("CENTRO DE IDIOMAS - CONSOLA".center(70))
        print("=" * 70)

    def mostrar_menu(self):
        print("""
        ┌─────────────────────────────────────────────────────┐
        │                 MENÚ PRINCIPAL                      │
        ├─────────────────────────────────────────────────────┤
        │  1) Consultar todos los alumnos                     │
        │  2) Registrar nuevo alumno                          │
        │  3) Actualizar datos de un alumno                   │
        │  4) Eliminar un alumno                              │
        │  0) Salir                                           │
        └─────────────────────────────────────────────────────┘
        """)

    def _procesar_resultado(self, raw_result):
        return json.loads(raw_result) if isinstance(raw_result, str) else raw_result

    def run(self):
        self.inicializar_bd()

        while True:
            clear()
            self.mostrar_banner()
            self.mostrar_menu()
            try:
                opc = input("  Selecciona una opción [1, 2, 3, 4, 0]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nSaliendo de forma segura...")
                break

            if opc == "1":
                self.op_consultar()
            elif opc == "2":
                self.op_crear()
            elif opc == "3":
                self.op_actualizar()
            elif opc == "4":
                self.op_eliminar()
            elif opc == "0":
                print("\nHasta luego.")
                break
            else:
                print("\nOpción no válida")

            try:
                input("\nPresiona ENTER para continuar...")
            except (KeyboardInterrupt, EOFError):
                print("\nSaliendo de forma segura...")
                break

    def inicializar_bd(self):
        sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Alumnos' and xtype='U')
        CREATE TABLE Alumnos (
            Id INT PRIMARY KEY,
            Nombre NVARCHAR(100) NOT NULL,
            Idioma NVARCHAR(50) NOT NULL,
            Nivel NVARCHAR(20) NOT NULL
        )
        """
        # Excepción intencional para la creación de tablas (sintaxis distinta)
        if "Postgresql" in self.nombre_clase_db:
             sql = """
             CREATE TABLE IF NOT EXISTS Alumnos (
                 Id INT PRIMARY KEY,
                 Nombre VARCHAR(100) NOT NULL,
                 Idioma VARCHAR(50) NOT NULL,
                 Nivel VARCHAR(20) NOT NULL
             )
             """
        self._ejecutar(sql)

    def op_consultar(self):
        clear()
        print("\nLISTADO DE ALUMNOS\n")

        sql = "SELECT Id, Nombre, Idioma, Nivel FROM Alumnos ORDER BY Id"
        raw_result = self._ejecutar(sql)
        result = self._procesar_resultado(raw_result)

        if result.get("estado"):
            rows = result.get("registros", [])
            print_table(rows, ["Id", "Nombre", "Idioma", "Nivel"])
        else:
            print(f"Error al consultar: {result.get('error') or result.get('mensaje')}")

    def op_crear(self):
        clear()
        print("\nREGISTRAR NUEVO ALUMNO\n")
        try:
            id_alumno = int(input("  ID del alumno: "))
            nombre = input("  Nombre completo: ").strip()
            idioma = input("  Idioma a cursar: ").strip()
            nivel = input("  Nivel: ").strip()

            if not nombre or not idioma or not nivel:
                print("Todos los campos son obligatorios.")
                return

            sql = "INSERT INTO Alumnos (Id, Nombre, Idioma, Nivel) VALUES (?, ?, ?, ?)"
            raw_result = self._ejecutar(sql, (id_alumno, nombre, idioma, nivel))
            result = self._procesar_resultado(raw_result)

            if result.get("estado"):
                print(f"\n{result.get('mensaje')}")
            else:
                print(f"\nError al registrar: {result.get('error') or result.get('mensaje')}")

        except ValueError:
            print("\nEl ID debe ser un número entero.")

    def op_actualizar(self):
        clear()
        print("\nACTUALIZAR DATOS DE ALUMNO\n")
        try:
            id_alumno = int(input("  Ingresa el ID del alumno a actualizar: "))

            # 1. Verificar si existe y mostrar datos actuales
            check_sql = "SELECT Nombre, Idioma, Nivel FROM Alumnos WHERE Id = ?"
            check_res = self._procesar_resultado(self._ejecutar(check_sql, (id_alumno,)))

            if not check_res.get("registros"):
                print("No se encontró ningún alumno con ese ID.")
                return

            alumno_actual = check_res['registros'][0]
            print(f"\n  Datos actuales:")
            print(f"  - Nombre: {alumno_actual['Nombre']}")
            print(f"  - Idioma: {alumno_actual['Idioma']}")
            print(f"  - Nivel:  {alumno_actual['Nivel']}\n")
            print("  (Presiona ENTER sin escribir nada para conservar el valor actual)\n")

            # 2. Pedir nuevos datos
            nuevo_nombre = input(f"  Nuevo Nombre [{alumno_actual['Nombre']}]: ").strip()
            nuevo_idioma = input(f"  Nuevo Idioma [{alumno_actual['Idioma']}]: ").strip()
            nuevo_nivel = input(f"  Nuevo Nivel [{alumno_actual['Nivel']}]: ").strip()

            # 3. Determinar qué valores se van a guardar
            nombre_final = nuevo_nombre if nuevo_nombre else alumno_actual['Nombre']
            idioma_final = nuevo_idioma if nuevo_idioma else alumno_actual['Idioma']
            nivel_final = nuevo_nivel if nuevo_nivel else alumno_actual['Nivel']

            # 4. Ejecutar el UPDATE
            sql = "UPDATE Alumnos SET Nombre = ?, Idioma = ?, Nivel = ? WHERE Id = ?"
            raw_result = self._ejecutar(sql, (nombre_final, idioma_final, nivel_final, id_alumno))
            result = self._procesar_resultado(raw_result)

            if result.get("estado"):
                print(f"\n{result.get('mensaje')} (Afectados: {result.get('filas_afectadas')})")
            else:
                print(f"\nError al actualizar: {result.get('error') or result.get('mensaje')}")

        except ValueError:
            print("\nEl ID debe ser un número entero.")

    def op_eliminar(self):
        clear()
        print("\nELIMINAR ALUMNO\n")
        try:
            id_alumno = int(input("  Ingresa el ID del alumno a eliminar: "))

            confirmacion = input(f"  ¿Estás seguro de eliminar el ID {id_alumno}? (s/n): ").strip().lower()
            if confirmacion != 's':
                print("Cancelado.")
                return

            sql = "DELETE FROM Alumnos WHERE Id = ?"
            raw_result = self._ejecutar(sql, (id_alumno,))
            result = self._procesar_resultado(raw_result)

            if result.get("estado") and result.get("filas_afectadas", 0) > 0:
                print(f"\n{result.get('mensaje')}")
            elif result.get("estado"):
                print("\nNo se encontró el alumno (0 filas afectadas).")
            else:
                print(f"\nError al eliminar: {result.get('error') or result.get('mensaje')}")

        except ValueError:
            print("\nEl ID debe ser un número entero.")