import json


class CrudIdiomas:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'idiomas'.
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

    def consultar_todos(self, solo_activos=False):
        """Retorna la lista de todos los idiomas registrados."""
        sql = "SELECT id_idioma, nombre, activo FROM idiomas"
        if solo_activos:
            sql += " WHERE activo = ? ORDER BY id_idioma"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY id_idioma"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_idioma):
        """Retorna un único idioma según su clave primaria."""
        sql = "SELECT id_idioma, nombre, activo FROM idiomas WHERE id_idioma = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_idioma,)))

    def crear(self, nombre, activo=True, **kwargs):
        """Registra un nuevo idioma en el catálogo."""
        if "estado" in kwargs:
            activo = kwargs["estado"]
        if not nombre or not str(nombre).strip():
            return {"estado": False, "mensaje": "El campo 'nombre' es obligatorio"}

        sql = "INSERT INTO idiomas (nombre, activo) VALUES (?, ?)"
        res = self._ejecutar(sql, (str(nombre).strip(), bool(activo)))
        return self._procesar_resultado(res)

    def actualizar(self, id_idioma, nombre=None, activo=None, **kwargs):
        """Actualiza los datos de un idioma existente."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_idioma)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el idioma con ID {id_idioma}"}

        actual = actual_res["registros"][0]
        nom_final = str(nombre).strip() if nombre is not None else actual["nombre"]
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = "UPDATE idiomas SET nombre = ?, activo = ? WHERE id_idioma = ?"
        res = self._ejecutar(sql, (nom_final, act_final, id_idioma))
        return self._procesar_resultado(res)

    def eliminar(self, id_idioma, baja_logica=True):
        """Elimina o desactiva un idioma (baja lógica por defecto)."""
        if baja_logica:
            sql = "UPDATE idiomas SET activo = ? WHERE id_idioma = ?"
            res = self._ejecutar(sql, (False, id_idioma))
        else:
            sql = "DELETE FROM idiomas WHERE id_idioma = ?"
            res = self._ejecutar(sql, (id_idioma,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_idioma, nuevo_estado):
        """Activa o desactiva un idioma (True/False)."""
        sql = "UPDATE idiomas SET activo = ? WHERE id_idioma = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_idioma))
        return self._procesar_resultado(res)
