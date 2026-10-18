import json


class CrudHorarios:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'horarios'.
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

    def _normalizar_horas(self, res):
        """Formatea hora_inicio y hora_fin a HH:MM para lectura uniforme."""
        if isinstance(res, dict) and res.get("registros"):
            for r in res["registros"]:
                for campo in ("hora_inicio", "hora_fin"):
                    if campo in r and r[campo] is not None:
                        r[campo] = str(r[campo])[:5]
        return res

    def consultar_todos(self):
        """Retorna la lista de todos los horarios registrados."""
        sql = "SELECT id_horario, dias, hora_inicio, hora_fin FROM horarios ORDER BY id_horario"
        return self._normalizar_horas(self._procesar_resultado(self._ejecutar(sql)))

    def consultar_por_id(self, id_horario):
        """Retorna un horario según su ID."""
        sql = "SELECT id_horario, dias, hora_inicio, hora_fin FROM horarios WHERE id_horario = ?"
        return self._normalizar_horas(self._procesar_resultado(self._ejecutar(sql, (id_horario,))))

    def crear(self, dias, hora_inicio, hora_fin, **kwargs):
        """Registra un nuevo bloque de horario (hora_fin > hora_inicio)."""
        if not dias or not hora_inicio or not hora_fin:
            return {"estado": False, "mensaje": "Campos obligatorios incompletos (dias, hora_inicio, hora_fin)"}

        sql = "INSERT INTO horarios (dias, hora_inicio, hora_fin) VALUES (?, ?, ?)"
        res = self._ejecutar(sql, (str(dias).strip(), str(hora_inicio).strip(), str(hora_fin).strip()))
        return self._procesar_resultado(res)

    def actualizar(self, id_horario, dias=None, hora_inicio=None, hora_fin=None, **kwargs):
        """Actualiza un horario existente."""
        actual_res = self.consultar_por_id(id_horario)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el horario con ID {id_horario}"}

        actual = actual_res["registros"][0]
        dias_final = str(dias).strip() if dias is not None else actual["dias"]
        ini_final = str(hora_inicio).strip() if hora_inicio is not None else str(actual["hora_inicio"])
        fin_final = str(hora_fin).strip() if hora_fin is not None else str(actual["hora_fin"])

        sql = "UPDATE horarios SET dias = ?, hora_inicio = ?, hora_fin = ? WHERE id_horario = ?"
        res = self._ejecutar(sql, (dias_final, ini_final, fin_final, id_horario))
        return self._procesar_resultado(res)

    def eliminar(self, id_horario, **kwargs):
        """Elimina un horario por su ID."""
        sql = "DELETE FROM horarios WHERE id_horario = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_horario,)))
