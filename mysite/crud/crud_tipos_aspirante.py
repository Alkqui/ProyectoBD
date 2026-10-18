import json


class CrudTiposAspirante:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'tipos_aspirante'.
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
        """Retorna la lista de todos los tipos de aspirante registrados."""
        sql = """
        SELECT id_tipo_aspirante, nombre_tipo, porcentaje_descuento
        FROM tipos_aspirante
        ORDER BY id_tipo_aspirante
        """
        return self._procesar_resultado(self._ejecutar(sql))

    def consultar_por_id(self, id_tipo_aspirante):
        """Retorna un tipo de aspirante según su ID."""
        sql = """
        SELECT id_tipo_aspirante, nombre_tipo, porcentaje_descuento
        FROM tipos_aspirante
        WHERE id_tipo_aspirante = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_tipo_aspirante,)))

    def crear(self, nombre_tipo, porcentaje_descuento=0.0, **kwargs):
        """Registra un nuevo tipo de aspirante con su porcentaje de descuento (0 a 100)."""
        if not nombre_tipo or not str(nombre_tipo).strip():
            return {"estado": False, "mensaje": "El campo 'nombre_tipo' es obligatorio"}

        sql = "INSERT INTO tipos_aspirante (nombre_tipo, porcentaje_descuento) VALUES (?, ?)"
        res = self._ejecutar(sql, (str(nombre_tipo).strip(), float(porcentaje_descuento)))
        return self._procesar_resultado(res)

    def actualizar(self, id_tipo_aspirante, nombre_tipo=None, porcentaje_descuento=None, **kwargs):
        """Actualiza un tipo de aspirante existente."""
        actual_res = self.consultar_por_id(id_tipo_aspirante)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el tipo de aspirante con ID {id_tipo_aspirante}"}

        actual = actual_res["registros"][0]
        nom_final = str(nombre_tipo).strip() if nombre_tipo is not None else actual["nombre_tipo"]
        desc_final = float(porcentaje_descuento) if porcentaje_descuento is not None else float(actual["porcentaje_descuento"])

        sql = """
        UPDATE tipos_aspirante
        SET nombre_tipo = ?, porcentaje_descuento = ?
        WHERE id_tipo_aspirante = ?
        """
        res = self._ejecutar(sql, (nom_final, desc_final, id_tipo_aspirante))
        return self._procesar_resultado(res)

    def eliminar(self, id_tipo_aspirante, **kwargs):
        """Elimina un tipo de aspirante por su ID."""
        sql = "DELETE FROM tipos_aspirante WHERE id_tipo_aspirante = ?"
        return self._procesar_resultado(self._ejecutar(sql, (id_tipo_aspirante,)))
