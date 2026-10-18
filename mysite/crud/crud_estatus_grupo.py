import json


class CrudEstatusGrupo:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'estatus_grupo'.
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
        """Retorna la lista de todos los estatus de grupo registrados."""
        sql = "SELECT id_estatus, tipo_estatus FROM estatus_grupo ORDER BY id_estatus"
        return self._procesar_resultado(self._ejecutar(sql))

    def consultar_por_id(self, id_estatus):
        """Retorna un estatus de grupo según su ID."""
        sql = "SELECT id_estatus, tipo_estatus FROM estatus_grupo WHERE id_estatus = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_estatus,)))

    def crear(self, tipo_estatus, **kwargs):
        """Registra un nuevo tipo de estatus en estatus_grupo."""
        if not tipo_estatus or not str(tipo_estatus).strip():
            return {"estado": False, "mensaje": "El campo 'tipo_estatus' es obligatorio"}

        sql = "INSERT INTO estatus_grupo (tipo_estatus) VALUES (?)"
        res = self._ejecutar(sql, (str(tipo_estatus).strip(),))
        return self._procesar_resultado(res)

    def actualizar(self, id_estatus, tipo_estatus=None, **kwargs):
        """Actualiza un estatus de grupo existente."""
        actual_res = self.consultar_por_id(id_estatus)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el estatus con ID {id_estatus}"}

        actual = actual_res["registros"][0]
        tip_final = str(tipo_estatus).strip() if tipo_estatus is not None else actual["tipo_estatus"]

        sql = "UPDATE estatus_grupo SET tipo_estatus = ? WHERE id_estatus = ?"
        res = self._ejecutar(sql, (tip_final, id_estatus))
        return self._procesar_resultado(res)

    def eliminar(self, id_estatus, **kwargs):
        """Elimina un estatus de grupo por su ID."""
        sql = "DELETE FROM estatus_grupo WHERE id_estatus = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_estatus,)))
