import hashlib
import json


class CrudUsuarios:
    """
    Clase de servicio/DAO para la gestión de la tabla maestra 'usuarios'.
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

    @staticmethod
    def _normalizar_hash(valor):
        """Asegura que la contraseña tenga formato hash (>= 32 caracteres) aplicando SHA-256 si es texto plano."""
        texto = str(valor or "").strip()
        if len(texto) < 32:
            return hashlib.sha256(texto.encode("utf-8")).hexdigest()
        return texto

    def consultar_todos(self, solo_activos=False):
        """Retorna la lista de todos los usuarios con su personal y rol asociado."""
        if "Postgresql" in self.nombre_clase_db:
            sql = """
            SELECT u.id_usuario, u.id_personal,
                   (p.nombre || ' ' || p.apellido_paterno) AS personal,
                   u.id_rol, r.nombre_rol AS rol,
                   u.nombre_usuario, u.contrasena_hash, u.ultimo_acceso, u.activo
            FROM usuarios u
            LEFT JOIN personal p ON u.id_personal = p.id_personal
            LEFT JOIN roles r ON u.id_rol = r.id_rol
            """
        else:
            sql = """
            SELECT u.id_usuario, u.id_personal,
                   (p.nombre + ' ' + p.apellido_paterno) AS personal,
                   u.id_rol, r.nombre_rol AS rol,
                   u.nombre_usuario, u.contrasena_hash, u.ultimo_acceso, u.activo
            FROM usuarios u
            LEFT JOIN personal p ON u.id_personal = p.id_personal
            LEFT JOIN roles r ON u.id_rol = r.id_rol
            """

        if solo_activos:
            sql += " WHERE u.activo = ? ORDER BY u.id_usuario"
            res = self._ejecutar(sql, (True,))
        else:
            sql += " ORDER BY u.id_usuario"
            res = self._ejecutar(sql)
        return self._procesar_resultado(res)

    def consultar_por_id(self, id_usuario):
        """Retorna un usuario según su ID."""
        sql = """
        SELECT u.id_usuario, u.id_personal, u.id_rol, r.nombre_rol AS rol,
               u.nombre_usuario, u.contrasena_hash, u.ultimo_acceso, u.activo
        FROM usuarios u
        LEFT JOIN roles r ON u.id_rol = r.id_rol
        WHERE u.id_usuario = ?
        """
        return self._procesar_resultado(self._ejecutar(sql, (id_usuario,)))

    def crear(self, id_personal, id_rol, nombre_usuario, contrasena_hash, activo=True, **kwargs):
        """Registra un nuevo usuario en el sistema."""
        if "estado" in kwargs:
            activo = kwargs["estado"]
        if id_personal is None or id_rol is None or not nombre_usuario or not contrasena_hash:
            return {
                "estado": False,
                "mensaje": "Campos obligatorios incompletos (id_personal, id_rol, nombre_usuario, contrasena_hash)"
            }

        hash_final = self._normalizar_hash(contrasena_hash)
        sql = """
        INSERT INTO usuarios (id_personal, id_rol, nombre_usuario, contrasena_hash, activo)
        VALUES (?, ?, ?, ?, ?)
        """
        parametros = (
            int(id_personal),
            int(id_rol),
            str(nombre_usuario).strip().lower(),
            hash_final,
            bool(activo),
        )
        res = self._ejecutar(sql, parametros)
        return self._procesar_resultado(res)

    def actualizar(self, id_usuario, id_personal=None, id_rol=None,
                   nombre_usuario=None, contrasena_hash=None, activo=None, **kwargs):
        """Actualiza los datos de un usuario existente."""
        if activo is None and "estado" in kwargs:
            activo = kwargs["estado"]

        actual_res = self.consultar_por_id(id_usuario)
        if not actual_res.get("estado") or not actual_res.get("registros"):
            return {"estado": False, "mensaje": f"No se encontró el usuario con ID {id_usuario}"}

        actual = actual_res["registros"][0]
        per_final = int(id_personal) if id_personal is not None else int(actual["id_personal"])
        rol_final = int(id_rol) if id_rol is not None else int(actual["id_rol"])
        usr_final = str(nombre_usuario).strip().lower() if nombre_usuario is not None else actual["nombre_usuario"]
        hsh_final = self._normalizar_hash(contrasena_hash) if contrasena_hash is not None else actual["contrasena_hash"]
        act_final = bool(activo) if activo is not None else bool(actual["activo"])

        sql = """
        UPDATE usuarios
        SET id_personal = ?, id_rol = ?, nombre_usuario = ?, contrasena_hash = ?, activo = ?
        WHERE id_usuario = ?
        """
        res = self._ejecutar(sql, (per_final, rol_final, usr_final, hsh_final, act_final, id_usuario))
        return self._procesar_resultado(res)

    def eliminar(self, id_usuario, baja_logica=True):
        """Elimina o desactiva un usuario (baja lógica por defecto)."""
        if baja_logica:
            sql = "UPDATE usuarios SET activo = ? WHERE id_usuario = ?"
            res = self._ejecutar(sql, (False, id_usuario))
        else:
            sql = "DELETE FROM usuarios WHERE id_usuario = ?"
            res = self._ejecutar(sql, (id_usuario,))
        return self._procesar_resultado(res)

    def cambiar_estado(self, id_usuario, nuevo_estado):
        """Activa o desactiva un usuario (True/False)."""
        sql = "UPDATE usuarios SET activo = ? WHERE id_usuario = ?"
        res = self._ejecutar(sql, (bool(nuevo_estado), id_usuario))
        return self._procesar_resultado(res)
