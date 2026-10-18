import json


class CrudGrupos:
    """
    Clase de servicio/DAO para la gestión de la tabla 'grupos'.
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
        """Retorna la lista de todos los grupos con curso, idioma, periodo, docente, horario, aula y estatus."""
        if "Postgresql" in self.nombre_clase_db:
            sql = """
            SELECT g.id_grupo, g.codigo_grupo, g.id_curso, g.id_idioma,
                   i.nombre AS idioma, g.id_periodo, p.nombre_periodo AS periodo,
                   g.id_docente, (d.nombres || ' ' || d.apellido_paterno) AS docente,
                   g.id_horario,
                   (h.dias || ' (' || to_char(h.hora_inicio, 'HH24:MI') || '-' || to_char(h.hora_fin, 'HH24:MI') || ')') AS horario,
                   g.id_aula, a.nombre_aula AS aula,
                   g.cupo_minimo, g.cupo_maximo, g.id_estatus, e.tipo_estatus AS estatus
            FROM grupos g
            LEFT JOIN idiomas i ON g.id_idioma = i.id_idioma
            LEFT JOIN periodos p ON g.id_periodo = p.id_periodo
            LEFT JOIN docentes d ON g.id_docente = d.id_docente
            LEFT JOIN horarios h ON g.id_horario = h.id_horario
            LEFT JOIN aulas a ON g.id_aula = a.id_aula
            LEFT JOIN estatus_grupo e ON g.id_estatus = e.id_estatus
            """
        else:
            sql = """
            SELECT g.id_grupo, g.codigo_grupo, g.id_curso, g.id_idioma,
                   i.nombre AS idioma, g.id_periodo, p.nombre_periodo AS periodo,
                   g.id_docente, (d.nombres + ' ' + d.apellido_paterno) AS docente,
                   g.id_horario,
                   (h.dias + ' (' + CONVERT(varchar(5), h.hora_inicio, 108) + '-' + CONVERT(varchar(5), h.hora_fin, 108) + ')') AS horario,
                   g.id_aula, a.nombre_aula AS aula,
                   g.cupo_minimo, g.cupo_maximo, g.id_estatus, e.tipo_estatus AS estatus
            FROM grupos g
            LEFT JOIN idiomas i ON g.id_idioma = i.id_idioma
            LEFT JOIN periodos p ON g.id_periodo = p.id_periodo
            LEFT JOIN docentes d ON g.id_docente = d.id_docente
            LEFT JOIN horarios h ON g.id_horario = h.id_horario
            LEFT JOIN aulas a ON g.id_aula = a.id_aula
            LEFT JOIN estatus_grupo e ON g.id_estatus = e.id_estatus
            """

        if solo_activos:
            sql += " WHERE g.id_estatus = 1 ORDER BY g.id_grupo"
            res = self._ejecutar(sql)
        else:
            sql += " ORDER BY g.id_grupo"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_grupo):
        """Retorna un único grupo según su ID."""
        sql = """
        SELECT g.id_grupo, g.codigo_grupo, g.id_curso, g.id_idioma,
               i.nombre AS idioma, g.id_periodo, p.nombre_periodo AS periodo,
               g.id_docente, g.id_horario, g.id_aula, a.nombre_aula AS aula,
               g.cupo_minimo, g.cupo_maximo, g.id_estatus, e.tipo_estatus AS estatus
        FROM grupos g
        LEFT JOIN idiomas i ON g.id_idioma = i.id_idioma
        LEFT JOIN periodos p ON g.id_periodo = p.id_periodo
        LEFT JOIN aulas a ON g.id_aula = a.id_aula
        LEFT JOIN estatus_grupo e ON g.id_estatus = e.id_estatus
        WHERE g.id_grupo = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_grupo,)))

    def _obtener_idioma_de_curso(self, id_curso, id_idioma_fallback=1):
        """Obtiene el id_idioma asociado al curso para cumplir fk_grupos_curso_idioma."""
        res = self._procesar_resultado(
            self._ejecutar("SELECT id_idioma FROM cursos WHERE id_curso = ?", (int(id_curso),))
        )
        if res.get("registros"):
            return int(res["registros"][0]["id_idioma"])
        return int(id_idioma_fallback or 1)

    def _asegurar_idioma_docente(self, id_docente, id_idioma):
        """Garantiza que exista la relación en idioma_docente para cumplir fk_grupos_docente_idioma."""
        existe = self._procesar_resultado(
            self._ejecutar(
                "SELECT id_idioma_docente FROM idioma_docente WHERE id_docente = ? AND id_idioma = ?",
                (int(id_docente), int(id_idioma))
            )
        )
        if not existe.get("registros"):
            self._ejecutar(
                "INSERT INTO idioma_docente (id_docente, id_idioma, es_principal) VALUES (?, ?, ?)",
                (int(id_docente), int(id_idioma), False)
            )

    def crear(self, codigo_grupo, id_curso, id_docente, id_horario,
              id_aula=1, id_periodo=4, id_idioma=None,
              cupo_minimo=5, cupo_maximo=25, id_estatus=1, **kwargs):
        """Registra un nuevo grupo operativo."""
        if not codigo_grupo or id_curso is None or id_docente is None or id_horario is None:
            return {
                "estado": False,
                "mensaje": "Campos obligatorios incompletos (codigo_grupo, id_curso, id_docente, id_horario)"
            }

        idioma_curso = self._obtener_idioma_de_curso(id_curso, id_idioma)
        self._asegurar_idioma_docente(id_docente, idioma_curso)

        sql = """
        INSERT INTO grupos (
            codigo_grupo, id_curso, id_idioma, id_periodo, id_docente,
            id_horario, id_aula, cupo_minimo, cupo_maximo, id_estatus
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        parametros = (
            str(codigo_grupo).strip().upper(),
            int(id_curso),
            int(idioma_curso),
            int(id_periodo),
            int(id_docente),
            int(id_horario),
            int(id_aula),
            int(cupo_minimo),
            int(cupo_maximo),
            int(id_estatus),
        )
        res = self._ejecutar(sql, parametros)
        return self._procesar_resultado(res)

    def actualizar(self, id_grupo, codigo_grupo=None, id_curso=None, id_idioma=None,
                   id_periodo=None, id_docente=None, id_horario=None, id_aula=None,
                   cupo_minimo=None, cupo_maximo=None, id_estatus=None, **kwargs):
        """Actualiza los datos de un grupo conservando los campos no provistos."""
        actual_res = self.consultar_por_id(id_grupo)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el grupo con ID {id_grupo}"}

        actual = actual_res["registros"][0]

        cod_final = str(codigo_grupo).strip().upper() if codigo_grupo is not None else actual["codigo_grupo"]
        cur_final = int(id_curso) if id_curso is not None else int(actual["id_curso"])
        idi_final = self._obtener_idioma_de_curso(cur_final, id_idioma or actual["id_idioma"])
        per_final = int(id_periodo) if id_periodo is not None else int(actual["id_periodo"])
        doc_final = int(id_docente) if id_docente is not None else int(actual["id_docente"])
        hor_final = int(id_horario) if id_horario is not None else int(actual["id_horario"])
        aul_final = int(id_aula) if id_aula is not None else int(actual["id_aula"])
        cmin_final = int(cupo_minimo) if cupo_minimo is not None else int(actual["cupo_minimo"])
        cmax_final = int(cupo_maximo) if cupo_maximo is not None else int(actual["cupo_maximo"])
        est_final = int(id_estatus) if id_estatus is not None else int(actual["id_estatus"])

        self._asegurar_idioma_docente(doc_final, idi_final)

        sql = """
        UPDATE grupos
        SET codigo_grupo = ?, id_curso = ?, id_idioma = ?, id_periodo = ?,
            id_docente = ?, id_horario = ?, id_aula = ?,
            cupo_minimo = ?, cupo_maximo = ?, id_estatus = ?
        WHERE id_grupo = ?
        """
        parametros = (
            cod_final, cur_final, idi_final, per_final,
            doc_final, hor_final, aul_final,
            cmin_final, cmax_final, est_final, id_grupo
        )
        res = self._ejecutar(sql, parametros)
        return self._procesar_resultado(res)

    def eliminar(self, id_grupo, baja_logica=True, estatus_cancelado=4):
        """
        Elimina o cancela un grupo.
        Por defecto realiza baja lógica cambiando su id_estatus a Cancelado (4).
        """
        if baja_logica:
            sql = "UPDATE grupos SET id_estatus = ? WHERE id_grupo = ?"
            res = self._ejecutar(sql, (estatus_cancelado, id_grupo))
        else:
            sql = "DELETE FROM grupos WHERE id_grupo = ?"
            res = self._ejecutar(sql, (id_grupo,))
        return self._procesar_resultado(res)

    def cambiar_estatus(self, id_grupo, nuevo_id_estatus):
        """Actualiza el estatus de un grupo (1=Activo, 2=En espera, 3=Cerrado, 4=Cancelado, 5=Finalizado)."""
        sql = "UPDATE grupos SET id_estatus = ? WHERE id_grupo = ?"
        res = self._ejecutar(sql, (int(nuevo_id_estatus), id_grupo))
        return self._procesar_resultado(res)
