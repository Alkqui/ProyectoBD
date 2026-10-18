import json


class CrudCursos:
    """
    Clase de servicio/DAO para la gestión de la tabla 'cursos'.
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
        """Retorna la lista de todos los cursos registrados con su idioma, nivel MCER, horas y costo."""
        sql = """
        SELECT c.id_curso, c.id_idioma, i.nombre AS idioma,
               c.id_nivel, n.numero_nivel, TRIM(n.equivalencia_mcer) AS equivalencia_mcer,
               c.horas_totales, c.costo, c.activo
        FROM cursos c
        LEFT JOIN idiomas i ON c.id_idioma = i.id_idioma
        LEFT JOIN niveles n ON c.id_nivel = n.id_nivel
        """
        if solo_activos:
            sql += " WHERE c.activo = ? ORDER BY c.id_curso"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY c.id_curso"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_curso):
        """Retorna un único curso según su ID."""
        sql = """
        SELECT c.id_curso, c.id_idioma, i.nombre AS idioma,
               c.id_nivel, n.numero_nivel, TRIM(n.equivalencia_mcer) AS equivalencia_mcer,
               c.horas_totales, c.costo, c.activo
        FROM cursos c
        LEFT JOIN idiomas i ON c.id_idioma = i.id_idioma
        LEFT JOIN niveles n ON c.id_nivel = n.id_nivel
        WHERE c.id_curso = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_curso,)))

    def crear(self, id_idioma, id_nivel, horas_totales=60, costo=1500.00, activo=True, **kwargs):
        """Registra un nuevo curso con horas_totales y costo."""
        if "estado" in kwargs:
            activo = kwargs["estado"]

        if id_idioma is None or id_nivel is None:
            return {"estado": False, "mensaje": "id_idioma e id_nivel son requeridos"}

        sql = """
        INSERT INTO cursos (id_idioma, id_nivel, horas_totales, costo, activo)
        VALUES (?, ?, ?, ?, ?)
        """
        res = self._ejecutar(sql, (int(id_idioma), int(id_nivel), int(horas_totales), float(costo), bool(activo)))
        return self._procesar_resultado(res)

    def actualizar(self, id_curso, id_idioma=None, id_nivel=None, horas_totales=None, costo=None, activo=None, **kwargs):
        """Actualiza los datos de un curso conservando los valores no provistos."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_curso)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el curso con ID {id_curso}"}

        actual = actual_res["registros"][0]

        idi_final = int(id_idioma) if id_idioma is not None else int(actual["id_idioma"])
        niv_final = int(id_nivel) if id_nivel is not None else int(actual["id_nivel"])
        hrs_final = int(horas_totales) if horas_totales is not None else int(actual["horas_totales"])
        cos_final = float(costo) if costo is not None else float(actual["costo"])
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE cursos
        SET id_idioma = ?, id_nivel = ?, horas_totales = ?, costo = ?, activo = ?
        WHERE id_curso = ?
        """
        res = self._ejecutar(sql, (idi_final, niv_final, hrs_final, cos_final, act_final, id_curso))
        return self._procesar_resultado(res)

    def eliminar(self, id_curso, baja_logica=True):
        """
        Elimina o da de baja a un curso.
        Por defecto realiza baja lógica (activo = False).
        """
        if baja_logica:
            sql = "UPDATE cursos SET activo = ? WHERE id_curso = ?"
            res = self._ejecutar(sql, (False, id_curso))
        else:
            sql = "DELETE FROM cursos WHERE id_curso = ?"
            res = self._ejecutar(sql, (id_curso,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_curso, nuevo_estado):
        """Activa o desactiva a un curso (True/False)."""
        sql = "UPDATE cursos SET activo = ? WHERE id_curso = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_curso))
        return self._procesar_resultado(res)
