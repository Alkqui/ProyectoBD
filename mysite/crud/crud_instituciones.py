import json


class CrudInstituciones:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'instituciones'.
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
        """Retorna la lista de todas las instituciones registradas."""
        sql = "SELECT id_institucion, nombre_institucion FROM instituciones ORDER BY id_institucion"
        return self._procesar_resultado(self._ejecutar(sql))

    def consultar_por_id(self, id_institucion):
        """Retorna una institución según su ID."""
        sql = "SELECT id_institucion, nombre_institucion FROM instituciones WHERE id_institucion = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_institucion,)))

    def crear(self, nombre_institucion, **kwargs):
        """Registra una nueva institución de procedencia."""
        if not nombre_institucion or not str(nombre_institucion).strip():
            return {"estado": False, "mensaje": "El campo 'nombre_institucion' es obligatorio"}

        sql = "INSERT INTO instituciones (nombre_institucion) VALUES (?)"
        res = self._ejecutar(sql, (str(nombre_institucion).strip(),))
        return self._procesar_resultado(res)

    def actualizar(self, id_institucion, nombre_institucion=None, **kwargs):
        """Actualiza el nombre de una institución existente."""
        actual_res = self.consultar_por_id(id_institucion)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró la institución con ID {id_institucion}"}

        actual = actual_res["registros"][0]
        nom_final = str(nombre_institucion).strip() if nombre_institucion is not None else actual["nombre_institucion"]

        sql = "UPDATE instituciones SET nombre_institucion = ? WHERE id_institucion = ?"
        res = self._ejecutar(sql, (nom_final, id_institucion))
        return self._procesar_resultado(res)

    def eliminar(self, id_institucion, **kwargs):
        """Elimina una institución por su ID."""
        sql = "DELETE FROM instituciones WHERE id_institucion = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_institucion,)))
