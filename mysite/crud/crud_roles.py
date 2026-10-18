import json


class CrudRoles:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'roles'.
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
        """Retorna la lista de todos los roles registrados."""
        sql = "SELECT id_rol, nombre_rol, descripcion FROM roles ORDER BY id_rol"
        return self._procesar_resultado(self._ejecutar(sql))

    def consultar_por_id(self, id_rol):
        """Retorna un rol según su ID."""
        sql = "SELECT id_rol, nombre_rol, descripcion FROM roles WHERE id_rol = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_rol,)))

    def crear(self, nombre_rol, descripcion=None, **kwargs):
        """Registra un nuevo rol en el sistema."""
        if not nombre_rol or not str(nombre_rol).strip():
            return {"estado": False, "mensaje": "El campo 'nombre_rol' es obligatorio"}

        sql = "INSERT INTO roles (nombre_rol, descripcion) VALUES (?, ?)"
        desc_val = str(descripcion).strip() if descripcion else None
        res = self._ejecutar(sql, (str(nombre_rol).strip(), desc_val))
        return self._procesar_resultado(res)

    def actualizar(self, id_rol, nombre_rol=None, descripcion=None, **kwargs):
        """Actualiza los datos de un rol existente."""
        actual_res = self.consultar_por_id(id_rol)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el rol con ID {id_rol}"}

        actual = actual_res["registros"][0]
        nom_final = str(nombre_rol).strip() if nombre_rol is not None else actual["nombre_rol"]
        desc_final = str(descripcion).strip() if descripcion is not None else actual["descripcion"]

        sql = "UPDATE roles SET nombre_rol = ?, descripcion = ? WHERE id_rol = ?"
        res = self._ejecutar(sql, (nom_final, desc_final, id_rol))
        return self._procesar_resultado(res)

    def eliminar(self, id_rol, **kwargs):
        """Elimina un rol por su ID."""
        sql = "DELETE FROM roles WHERE id_rol = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_rol,)))
