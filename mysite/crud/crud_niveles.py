import json


class CrudNiveles:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'niveles'.
    """

    def __init__(self, db_conexion):
        self.db = db_conexion
        self.nombre_clase_db = type(self.db).__name__

    def _ejecutar(self, sql, parametros=None):
        if "Postgresql" in self.nombre_clase_db:
            sql = sql.replace("?", "%s")
        if hasattr(self.db, "ejecutar_consulta"):
            return self.db.ejecutar_consulta(sql, parametros)
        return self.db.ejecutar_consultas(sql, parametros)

    def _procesar_resultado(self, raw_result):
        if isinstance(raw_result, str):
            try:
                return json.loads(raw_result)
            except Exception:
                return {"estado": False, "error": "Error al parsear respuesta JSON", "raw": raw_result}
        return raw_result if isinstance(raw_result, dict) else {"estado": False, "error": "Formato de respuesta desconocido"}

    def consultar_todos(self):
        """Retorna la lista de todos los niveles registrados."""
        sql = """
        SELECT id_nivel, numero_nivel, TRIM(equivalencia_mcer) AS equivalencia_mcer
        FROM niveles
        ORDER BY numero_nivel
        """
        return self._procesar_resultado(self._ejecutar(sql))

    def consultar_por_id(self, id_nivel):
        """Retorna un único nivel según su clave primaria."""
        sql = """
        SELECT id_nivel, numero_nivel, TRIM(equivalencia_mcer) AS equivalencia_mcer
        FROM niveles
        WHERE id_nivel = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_nivel,)))

    def crear(self, numero_nivel, equivalencia_mcer, **kwargs):
        """Registra un nuevo nivel en el catálogo (ej. numero_nivel=1, equivalencia_mcer='A1')."""
        if numero_nivel is None or not equivalencia_mcer:
            return {"estado": False, "mensaje": "Campos obligatorios incompletos (numero_nivel, equivalencia_mcer)"}

        sql = "INSERT INTO niveles (numero_nivel, equivalencia_mcer) VALUES (?, ?)"
        res = self._ejecutar(sql, (int(numero_nivel), str(equivalencia_mcer).strip().upper()))
        return self._procesar_resultado(res)

    def actualizar(self, id_nivel, numero_nivel=None, equivalencia_mcer=None, **kwargs):
        """Actualiza los datos de un nivel existente."""
        actual_res = self.consultar_por_id(id_nivel)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el nivel con ID {id_nivel}"}

        actual = actual_res["registros"][0]
        num_final = int(numero_nivel) if numero_nivel is not None else int(actual["numero_nivel"])
        mcer_final = str(equivalencia_mcer).strip().upper() if equivalencia_mcer is not None else actual["equivalencia_mcer"]

        sql = "UPDATE niveles SET numero_nivel = ?, equivalencia_mcer = ? WHERE id_nivel = ?"
        res = self._ejecutar(sql, (num_final, mcer_final, id_nivel))
        return self._procesar_resultado(res)

    def eliminar(self, id_nivel, **kwargs):
        """Elimina un nivel por su ID."""
        sql = "DELETE FROM niveles WHERE id_nivel = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_nivel,)))
