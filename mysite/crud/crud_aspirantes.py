import json


class CrudAspirantes:

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
        """Retorna la lista de todos los aspirantes registrados."""
        sql = """
        SELECT a.id_aspirante, a.nombres, a.apellido_paterno, a.apellido_materno,
               TRIM(a.curp) AS curp, a.fecha_nacimiento, a.correo_electronico,
               TRIM(a.telefono) AS telefono, a.fecha_registro,
               a.id_tipo_aspirante, t.nombre_tipo AS tipo_aspirante, a.activo
        FROM aspirantes a
        LEFT JOIN tipos_aspirante t ON a.id_tipo_aspirante = t.id_tipo_aspirante
        """
        if solo_activos:
            sql += " WHERE a.activo = ? ORDER BY a.id_aspirante"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY a.id_aspirante"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_aspirante):
        """Retorna un único aspirante según su clave primaria."""
        sql = """
        SELECT a.id_aspirante, a.nombres, a.apellido_paterno, a.apellido_materno,
               TRIM(a.curp) AS curp, a.fecha_nacimiento, a.correo_electronico,
               TRIM(a.telefono) AS telefono, a.fecha_registro,
               a.id_tipo_aspirante, t.nombre_tipo AS tipo_aspirante, a.activo
        FROM aspirantes a
        LEFT JOIN tipos_aspirante t ON a.id_tipo_aspirante = t.id_tipo_aspirante
        WHERE a.id_aspirante = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_aspirante,)))

    def crear(self, nombres, apellido_paterno, correo_electronico, telefono,
              curp, fecha_nacimiento="2000-01-01", id_tipo_aspirante=1,
              apellido_materno=None, activo=True, **kwargs):
        """Registra un nuevo aspirante bajo el nuevo esquema de base de datos."""
        if "id_tipoaspirante" in kwargs and id_tipo_aspirante == 1:
            id_tipo_aspirante = kwargs["id_tipoaspirante"]
        if "estado" in kwargs:
            activo = kwargs["estado"]

        if not nombres or not apellido_paterno or not correo_electronico or not telefono or not curp:
            return {
                "estado": False,
                "mensaje": "Campos obligatorios incompletos (nombres, apellido_paterno, curp, correo_electronico, telefono)"
            }

        sql = """
        INSERT INTO aspirantes (
            nombres, apellido_paterno, apellido_materno, curp, fecha_nacimiento,
            correo_electronico, telefono, id_tipo_aspirante, activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        parametros = (
            str(nombres).strip(),
            str(apellido_paterno).strip(),
            str(apellido_materno).strip() if apellido_materno else None,
            str(curp).strip().upper(),
            str(fecha_nacimiento).strip(),
            str(correo_electronico).strip(),
            str(telefono).strip(),
            int(id_tipo_aspirante),
            bool(activo),
        )
        res = self._ejecutar(sql, parametros)
        return self._procesar_resultado(res)

    def actualizar(self, id_aspirante, nombres=None, apellido_paterno=None,
                   apellido_materno=None, curp=None, fecha_nacimiento=None,
                   correo_electronico=None, telefono=None, id_tipo_aspirante=None,
                   activo=None, **kwargs):
        """Actualiza los datos de un aspirante existente conservando los valores no provistos."""
        if id_tipo_aspirante is None and "id_tipoaspirante" in kwargs:
            id_tipo_aspirante = kwargs["id_tipoaspirante"]
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_aspirante)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el aspirante con ID {id_aspirante}"}

        actual = actual_res["registros"][0]

        nom_final = str(nombres).strip() if nombres is not None else actual["nombres"]
        pat_final = str(apellido_paterno).strip() if apellido_paterno is not None else actual["apellido_paterno"]
        mat_final = str(apellido_materno).strip() if apellido_materno is not None else actual["apellido_materno"]
        curp_final = str(curp).strip().upper() if curp is not None else actual["curp"]
        nac_final = str(fecha_nacimiento).strip() if fecha_nacimiento is not None else str(actual["fecha_nacimiento"])
        cor_final = str(correo_electronico).strip() if correo_electronico is not None else actual["correo_electronico"]
        tel_final = str(telefono).strip() if telefono is not None else actual["telefono"]
        tip_final = int(id_tipo_aspirante) if id_tipo_aspirante is not None else int(actual["id_tipo_aspirante"])
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE aspirantes
        SET nombres = ?, apellido_paterno = ?, apellido_materno = ?,
            curp = ?, fecha_nacimiento = ?, correo_electronico = ?,
            telefono = ?, id_tipo_aspirante = ?, activo = ?
        WHERE id_aspirante = ?
        """
        parametros = (
            nom_final, pat_final, mat_final, curp_final, nac_final,
            cor_final, tel_final, tip_final, act_final, id_aspirante
        )
        res = self._ejecutar(sql, parametros)
        return self._procesar_resultado(res)

    def eliminar(self, id_aspirante, baja_logica=True):
        """
        Elimina o da de baja a un aspirante.
        Por defecto realiza baja lógica (activo = False) para proteger la integridad referencial.
        """
        if baja_logica:
            sql = "UPDATE aspirantes SET activo = ? WHERE id_aspirante = ?"
            res = self._ejecutar(sql, (False, id_aspirante))
        else:
            sql = "DELETE FROM aspirantes WHERE id_aspirante = ?"
            res = self._ejecutar(sql, (id_aspirante,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_aspirante, nuevo_estado):
        """Activa o desactiva a un aspirante (True/False)."""
        sql = "UPDATE aspirantes SET activo = ? WHERE id_aspirante = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_aspirante))
        return self._procesar_resultado(res)
