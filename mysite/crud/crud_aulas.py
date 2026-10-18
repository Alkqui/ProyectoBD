import json


class CrudAulas:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'aulas'.
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
        """Retorna la lista de todas las aulas registradas."""
        sql = "SELECT id_aula, nombre_aula, edificio, capacidad, activo FROM aulas"
        if solo_activos:
            sql += " WHERE activo = ? ORDER BY id_aula"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY id_aula"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_aula):
        """Retorna un aula según su ID."""
        sql = "SELECT id_aula, nombre_aula, edificio, capacidad, activo FROM aulas WHERE id_aula = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_aula,)))

    def crear(self, nombre_aula, edificio, capacidad=30, activo=True, **kwargs):
        """Registra una nueva aula física."""
        if "estado" in kwargs:
            activo = kwargs["estado"]
        if not nombre_aula or not edificio or capacidad is None:
            return {"estado": False, "mensaje": "Campos obligatorios incompletos (nombre_aula, edificio, capacidad)"}

        sql = "INSERT INTO aulas (nombre_aula, edificio, capacidad, activo) VALUES (?, ?, ?, ?)"
        res = self._ejecutar(sql, (str(nombre_aula).strip(), str(edificio).strip(), int(capacidad), bool(activo)))
        return self._procesar_resultado(res)

    def actualizar(self, id_aula, nombre_aula=None, edificio=None, capacidad=None, activo=None, **kwargs):
        """Actualiza los datos de un aula existente."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_aula)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el aula con ID {id_aula}"}

        actual = actual_res["registros"][0]
        nom_final = str(nombre_aula).strip() if nombre_aula is not None else actual["nombre_aula"]
        edi_final = str(edificio).strip() if edificio is not None else actual["edificio"]
        cap_final = int(capacidad) if capacidad is not None else int(actual["capacidad"])
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE aulas
        SET nombre_aula = ?, edificio = ?, capacidad = ?, activo = ?
        WHERE id_aula = ?
        """
        res = self._ejecutar(sql, (nom_final, edi_final, cap_final, act_final, id_aula))
        return self._procesar_resultado(res)

    def eliminar(self, id_aula, baja_logica=True):
        """Elimina o desactiva un aula (baja lógica por defecto)."""
        if baja_logica:
            sql = "UPDATE aulas SET activo = ? WHERE id_aula = ?"
            res = self._ejecutar(sql, (False, id_aula))
        else:
            sql = "DELETE FROM aulas WHERE id_aula = ?"
            res = self._ejecutar(sql, (id_aula,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_aula, nuevo_estado):
        """Activa o desactiva un aula (True/False)."""
        sql = "UPDATE aulas SET activo = ? WHERE id_aula = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_aula))
        return self._procesar_resultado(res)
