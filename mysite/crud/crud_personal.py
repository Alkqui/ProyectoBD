import json


class CrudPersonal:
    """
    Clase de servicio/DAO para la gestión de la tabla 'personal'.
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
        """Asegura que la respuesta sea un diccionario Python manipulable."""
        if isinstance(raw_result, str):
            try:
                return json.loads(raw_result)
            except Exception:
                return {"estado": False, "error": "Error al parsear respuesta JSON", "raw": raw_result}
        return raw_result if isinstance(raw_result, dict) else {"estado": False, "error": "Formato de respuesta desconocido"}

    def consultar_todos(self, solo_activos=False):
        """Retorna la lista de todo el personal administrativo registrado."""
        sql = """
        SELECT id_personal, nombre, apellido_paterno, apellido_materno, correo_institucional, activo
        FROM personal
        """
        if solo_activos:
            sql += " WHERE activo = ? ORDER BY id_personal"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY id_personal"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_personal):
        """Retorna un miembro de personal según su ID."""
        sql = """
        SELECT id_personal, nombre, apellido_paterno, apellido_materno, correo_institucional, activo
        FROM personal
        WHERE id_personal = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_personal,)))

    def obtener_siguiente_id(self):
        """Retorna el siguiente ID entero sugerido (MAX + 1)."""
        res = self._procesar_resultado(self._ejecutar("SELECT MAX(id_personal) AS max_id FROM personal"))
        if res.get("estado") and res.get("registros") and res["registros"][0].get("max_id"):
            try:
                return int(res["registros"][0]["max_id"]) + 1
            except Exception:
                return 1
        return 1

    def crear(self, nombre, apellido_paterno, correo_institucional, apellido_materno=None, activo=True, **kwargs):
        """Registra un nuevo miembro del personal."""
        if "estado" in kwargs:
            activo = kwargs["estado"]

        if not nombre or not apellido_paterno or not correo_institucional:
            return {
                "estado": False,
                "mensaje": "Campos obligatorios incompletos (nombre, apellido_paterno, correo_institucional)"
            }

        sql = """
        INSERT INTO personal (nombre, apellido_paterno, apellido_materno, correo_institucional, activo)
        VALUES (?, ?, ?, ?, ?)
        """
        parametros = (
            str(nombre).strip(),
            str(apellido_paterno).strip(),
            str(apellido_materno).strip() if apellido_materno else None,
            str(correo_institucional).strip(),
            bool(activo),
        )
        res = self._ejecutar(sql, parametros)
        return self._procesar_resultado(res)

    def actualizar(self, id_personal, nombre=None, apellido_paterno=None, apellido_materno=None,
                   correo_institucional=None, activo=None, **kwargs):
        """Actualiza los datos de un miembro del personal conservando los campos no provistos."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_personal)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró personal con ID {id_personal}"}

        actual = actual_res["registros"][0]

        nom_final = str(nombre).strip() if nombre is not None else actual["nombre"]
        pat_final = str(apellido_paterno).strip() if apellido_paterno is not None else actual["apellido_paterno"]
        mat_final = str(apellido_materno).strip() if apellido_materno is not None else actual["apellido_materno"]
        cor_final = str(correo_institucional).strip() if correo_institucional is not None else actual["correo_institucional"]
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE personal
        SET nombre = ?, apellido_paterno = ?, apellido_materno = ?,
            correo_institucional = ?, activo = ?
        WHERE id_personal = ?
        """
        res = self._ejecutar(sql, (nom_final, pat_final, mat_final, cor_final, act_final, id_personal))
        return self._procesar_resultado(res)

    def eliminar(self, id_personal, baja_logica=True):
        """
        Elimina o da de baja a un miembro de personal.
        Por defecto realiza baja lógica (activo = False).
        """
        if baja_logica:
            sql = "UPDATE personal SET activo = ? WHERE id_personal = ?"
            res = self._ejecutar(sql, (False, id_personal))
        else:
            sql = "DELETE FROM personal WHERE id_personal = ?"
            res = self._ejecutar(sql, (id_personal,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_personal, nuevo_estado):
        """Activa o desactiva al personal (True/False)."""
        sql = "UPDATE personal SET activo = ? WHERE id_personal = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_personal))
        return self._procesar_resultado(res)
