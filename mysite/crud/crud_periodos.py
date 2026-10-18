import json


class CrudPeriodos:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'periodos'.
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
        """Retorna la lista de todos los periodos escolares registrados."""
        sql = "SELECT id_periodo, nombre_periodo, fecha_inicio, fecha_fin, activo FROM periodos"
        if solo_activos:
            sql += " WHERE activo = ? ORDER BY id_periodo"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY id_periodo"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_periodo):
        """Retorna un periodo escolar según su ID."""
        sql = "SELECT id_periodo, nombre_periodo, fecha_inicio, fecha_fin, activo FROM periodos WHERE id_periodo = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_periodo,)))

    def crear(self, nombre_periodo, fecha_inicio, fecha_fin, activo=True, **kwargs):
        """Registra un nuevo periodo escolar (fecha_fin debe ser mayor a fecha_inicio)."""
        if "estado" in kwargs:
            activo = kwargs["estado"]
        if not nombre_periodo or not fecha_inicio or not fecha_fin:
            return {"estado": False, "mensaje": "Campos obligatorios incompletos (nombre_periodo, fecha_inicio, fecha_fin)"}

        sql = """
        INSERT INTO periodos (nombre_periodo, fecha_inicio, fecha_fin, activo)
        VALUES (?, ?, ?, ?)
        """
        res = self._ejecutar(sql, (str(nombre_periodo).strip(), str(fecha_inicio).strip(), str(fecha_fin).strip(), bool(activo)))
        return self._procesar_resultado(res)

    def actualizar(self, id_periodo, nombre_periodo=None, fecha_inicio=None, fecha_fin=None, activo=None, **kwargs):
        """Actualiza los datos de un periodo escolar existente."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_periodo)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el periodo con ID {id_periodo}"}

        actual = actual_res["registros"][0]
        nom_final = str(nombre_periodo).strip() if nombre_periodo is not None else actual["nombre_periodo"]
        ini_final = str(fecha_inicio).strip() if fecha_inicio is not None else str(actual["fecha_inicio"])
        fin_final = str(fecha_fin).strip() if fecha_fin is not None else str(actual["fecha_fin"])
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE periodos
        SET nombre_periodo = ?, fecha_inicio = ?, fecha_fin = ?, activo = ?
        WHERE id_periodo = ?
        """
        res = self._ejecutar(sql, (nom_final, ini_final, fin_final, act_final, id_periodo))
        return self._procesar_resultado(res)

    def eliminar(self, id_periodo, baja_logica=True):
        """Elimina o desactiva un periodo escolar (baja lógica por defecto)."""
        if baja_logica:
            sql = "UPDATE periodos SET activo = ? WHERE id_periodo = ?"
            res = self._ejecutar(sql, (False, id_periodo))
        else:
            sql = "DELETE FROM periodos WHERE id_periodo = ?"
            res = self._ejecutar(sql, (id_periodo,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_periodo, nuevo_estado):
        """Activa o desactiva un periodo escolar (True/False)."""
        sql = "UPDATE periodos SET activo = ? WHERE id_periodo = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_periodo))
        return self._procesar_resultado(res)
