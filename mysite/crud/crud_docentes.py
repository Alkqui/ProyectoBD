import json


class CrudDocentes:
    """
    Clase de servicio/DAO para la gestión de la tabla 'docentes' y su relación
    con 'instituciones' e 'idioma_docente'.
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
        """Retorna la lista de todos los docentes con su institución e idioma principal."""
        sql = """
        SELECT d.id_docente, d.nombres, d.apellido_paterno, d.apellido_materno,
               d.correo_electronico, d.id_institucion,
               inst.nombre_institucion AS institucion,
               idoc.id_idioma, i.nombre AS idioma_principal,
               d.activo
        FROM docentes d
        LEFT JOIN instituciones inst ON d.id_institucion = inst.id_institucion
        LEFT JOIN idioma_docente idoc ON d.id_docente = idoc.id_docente AND idoc.es_principal = ?
        LEFT JOIN idiomas i ON idoc.id_idioma = i.id_idioma
        """
        if solo_activos:
            sql += " WHERE d.activo = ? ORDER BY d.id_docente"
            res = self._ejecutar(sql, (True, True))
        else:
            sql += " ORDER BY d.id_docente"
            res = self._ejecutar(sql, (True,))
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_docente):
        """Retorna un único docente según su ID."""
        sql = """
        SELECT d.id_docente, d.nombres, d.apellido_paterno, d.apellido_materno,
               d.correo_electronico, d.id_institucion,
               inst.nombre_institucion AS institucion,
               idoc.id_idioma, i.nombre AS idioma_principal,
               d.activo
        FROM docentes d
        LEFT JOIN instituciones inst ON d.id_institucion = inst.id_institucion
        LEFT JOIN idioma_docente idoc ON d.id_docente = idoc.id_docente AND idoc.es_principal = ?
        LEFT JOIN idiomas i ON idoc.id_idioma = i.id_idioma
        WHERE d.id_docente = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (True, id_docente)))

    def _sincronizar_idioma_principal(self, id_docente, id_idioma):
        """Registra o actualiza el idioma principal del docente en idioma_docente."""
        if id_idioma is None:
            return
        id_idioma = int(id_idioma)
        existe = self._procesar_resultado(
            self._ejecutar(
                "SELECT id_idioma_docente FROM idioma_docente WHERE id_docente = ? AND id_idioma = ?",
                (id_docente, id_idioma)
            )
        )
        self._ejecutar(
            "UPDATE idioma_docente SET es_principal = ? WHERE id_docente = ?",
            (False, id_docente)
        )
        if existe.get("registros"):
            self._ejecutar(
                "UPDATE idioma_docente SET es_principal = ? WHERE id_docente = ? AND id_idioma = ?",
                (True, id_docente, id_idioma)
            )
        else:
            self._ejecutar(
                "INSERT INTO idioma_docente (id_docente, id_idioma, es_principal) VALUES (?, ?, ?)",
                (id_docente, id_idioma, True)
            )

    def crear(self, nombres, apellido_paterno, correo_electronico, id_institucion=1,
              apellido_materno=None, id_idioma=1, activo=True, **kwargs):
        """Registra un nuevo docente y su idioma principal en idioma_docente."""
        if "estado" in kwargs:
            activo = kwargs["estado"]

        if not nombres or not apellido_paterno or not correo_electronico or not id_institucion:
            return {
                "estado": False,
                "mensaje": "Campos obligatorios incompletos (nombres, apellido_paterno, correo_electronico, id_institucion)"
            }

        sql = """
        INSERT INTO docentes (nombres, apellido_paterno, apellido_materno, correo_electronico, id_institucion, activo)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        parametros = (
            str(nombres).strip(),
            str(apellido_paterno).strip(),
            str(apellido_materno).strip() if apellido_materno else None,
            str(correo_electronico).strip(),
            int(id_institucion),
            bool(activo),
        )
        res = self._procesar_resultado(self._ejecutar(sql, parametros))
        if res.get("estado") and id_idioma is not None:
            busq = self._procesar_resultado(
                self._ejecutar(
                    "SELECT id_docente FROM docentes WHERE correo_electronico = ?",
                    (str(correo_electronico).strip(),)
                )
            )
            if busq.get("registros"):
                nuevo_id = busq["registros"][0]["id_docente"]
                self._sincronizar_idioma_principal(nuevo_id, id_idioma)
        return res

    def actualizar(self, id_docente, nombres=None, apellido_paterno=None, apellido_materno=None,
                   correo_electronico=None, id_institucion=None, id_idioma=None, activo=None, **kwargs):
        """Actualiza los datos de un docente conservando los campos no provistos."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_docente)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el docente con ID {id_docente}"}

        actual = actual_res["registros"][0]

        nom_final = str(nombres).strip() if nombres is not None else actual["nombres"]
        pat_final = str(apellido_paterno).strip() if apellido_paterno is not None else actual["apellido_paterno"]
        mat_final = str(apellido_materno).strip() if apellido_materno is not None else actual["apellido_materno"]
        cor_final = str(correo_electronico).strip() if correo_electronico is not None else actual["correo_electronico"]
        ins_final = int(id_institucion) if id_institucion is not None else int(actual["id_institucion"])
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE docentes
        SET nombres = ?, apellido_paterno = ?, apellido_materno = ?,
            correo_electronico = ?, id_institucion = ?, activo = ?
        WHERE id_docente = ?
        """
        res = self._procesar_resultado(
            self._ejecutar(sql, (nom_final, pat_final, mat_final, cor_final, ins_final, act_final, id_docente))
        )
        if res.get("estado") and id_idioma is not None:
            self._sincronizar_idioma_principal(id_docente, id_idioma)
        return res

    def eliminar(self, id_docente, baja_logica=True):
        """
        Elimina o da de baja a un docente.
        Por defecto realiza baja lógica (activo = False).
        """
        if baja_logica:
            sql = "UPDATE docentes SET activo = ? WHERE id_docente = ?"
            res = self._ejecutar(sql, (False, id_docente))
        else:
            self._ejecutar("DELETE FROM idioma_docente WHERE id_docente = ?", (id_docente,))
            sql = "DELETE FROM docentes WHERE id_docente = ?"
            res = self._ejecutar(sql, (id_docente,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_docente, nuevo_estado):
        """Activa o desactiva a un docente (True/False)."""
        sql = "UPDATE docentes SET activo = ? WHERE id_docente = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_docente))
        return self._procesar_resultado(res)
