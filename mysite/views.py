"""
Vistas del proyecto.

- index(): sirve la página (templates/index.html).
- api():   puerta de entrada JSON que usa TUS clases CrudXxx.
"""
import inspect
import json
import os

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from mysite.conexiones.conexion_postgresql import ConexionPostgresql
from mysite.conexiones.conexion_sql_server import Conexion_sql_server
from mysite.crud import (
    CrudAspirantes,
    CrudAulas,
    CrudCursos,
    CrudDocentes,
    CrudEstatusGrupo,
    CrudGrupos,
    CrudHorarios,
    CrudIdiomas,
    CrudInstituciones,
    CrudNiveles,
    CrudPeriodos,
    CrudPersonal,
    CrudRoles,
    CrudTiposAspirante,
    CrudUsuarios,
)

# ---------------------------------------------------------------------------
# Configuración por módulo
#   estado_bool: la columna 'activo' es booleana (True/False) en la BD y el
#                HTML la muestra como "Activo"/"Inactivo".
#   metodo_estado: método del CRUD que cambia el estado/estatus (o None).
# ---------------------------------------------------------------------------
MODULOS = {
    "aspirantes":      {"clase": CrudAspirantes,     "pk": "id_aspirante",      "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "docentes":        {"clase": CrudDocentes,       "pk": "id_docente",        "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "personal":        {"clase": CrudPersonal,       "pk": "id_personal",       "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "cursos":          {"clase": CrudCursos,         "pk": "id_curso",          "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "grupos":          {"clase": CrudGrupos,         "pk": "id_grupo",          "estado_bool": False, "metodo_estado": "cambiar_estatus"},
    "idiomas":         {"clase": CrudIdiomas,        "pk": "id_idioma",         "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "niveles":         {"clase": CrudNiveles,        "pk": "id_nivel",          "estado_bool": False, "metodo_estado": None},
    "tipos_aspirante": {"clase": CrudTiposAspirante, "pk": "id_tipo_aspirante", "estado_bool": False, "metodo_estado": None},
    "instituciones":   {"clase": CrudInstituciones,  "pk": "id_institucion",    "estado_bool": False, "metodo_estado": None},
    "aulas":           {"clase": CrudAulas,          "pk": "id_aula",           "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "periodos":        {"clase": CrudPeriodos,       "pk": "id_periodo",        "estado_bool": True,  "metodo_estado": "cambiar_estado"},
    "horarios":        {"clase": CrudHorarios,       "pk": "id_horario",        "estado_bool": False, "metodo_estado": None},
    "estatus_grupo":   {"clase": CrudEstatusGrupo,   "pk": "id_estatus",        "estado_bool": False, "metodo_estado": None},
    "roles":           {"clase": CrudRoles,          "pk": "id_rol",            "estado_bool": False, "metodo_estado": None},
    "usuarios":        {"clase": CrudUsuarios,       "pk": "id_usuario",        "estado_bool": True,  "metodo_estado": "cambiar_estado"},
}

ACCIONES_POST = {"crear", "actualizar", "estado", "eliminar"}


# ---------------------------------------------------------------------------
# Conexión: se elige el motor con la variable MOTOR_BD del .env
#   MOTOR_BD=postgresql  (por defecto)
#   MOTOR_BD=sqlserver
# ---------------------------------------------------------------------------
def abrir_conexion():
    motor = os.environ.get("MOTOR_BD", "postgresql").strip().lower()
    cnn = Conexion_sql_server() if motor == "sqlserver" else ConexionPostgresql()
    if cnn.crear_conexion() is None:
        return None
    return cnn


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _a_bool(valor):
    return str(valor).strip().lower() in ("activo", "true", "1")


def _estado_a_texto(res, cfg):
    """True/False de la BD -> 'Activo'/'Inactivo' para el HTML."""
    if cfg["estado_bool"] and isinstance(res, dict):
        for fila in res.get("registros") or []:
            for campo in ("activo", "estado"):
                if campo in fila and fila[campo] in (True, False, 1, 0):
                    fila[campo] = "Activo" if bool(fila[campo]) else "Inactivo"
    return res


def _filtrar(metodo, datos, excluir=None):
    """Deja solo los datos que el método del CRUD realmente recibe."""
    sig = inspect.signature(metodo)
    acepta_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )
    permitidos = sig.parameters
    return {
        k: v for k, v in datos.items()
        if (acepta_kwargs or k in permitidos) and k != excluir
    }


def _normalizar_datos_entrada(datos, cfg):
    """Normaliza valores booleanos de estado y extrae IDs numéricos de cadenas 'ID - Texto'."""
    limpios = dict(datos)
    if cfg["estado_bool"]:
        for campo in ("activo", "estado"):
            if campo in limpios:
                limpios[campo] = _a_bool(limpios[campo])

    for k, v in list(limpios.items()):
        if k.startswith("id_") and isinstance(v, str) and " - " in v:
            parte_id = v.split(" - ", 1)[0].strip()
            if parte_id.isdigit():
                limpios[k] = int(parte_id)
    return limpios


def _llamar(modulo, accion, pk, datos):
    cfg = MODULOS[modulo]
    cnn = abrir_conexion()
    if cnn is None:
        return {"estado": False, "mensaje": "No fue posible conectarse a la base de datos"}

    try:
        crud = cfg["clase"](cnn)
        datos = _normalizar_datos_entrada(datos, cfg)

        if accion == "listar":
            res = crud.consultar_todos()
        elif accion == "detalle":
            res = crud.consultar_por_id(pk)
        elif accion == "crear":
            res = crud.crear(**_filtrar(crud.crear, datos))
        elif accion == "actualizar":
            res = crud.actualizar(pk, **_filtrar(crud.actualizar, datos, excluir=cfg["pk"]))
        elif accion == "estado":
            if not cfg["metodo_estado"]:
                return {"estado": False, "mensaje": "Esta tabla no maneja cambio de estado directo"}
            nuevo = datos.get("nuevo")
            if cfg["estado_bool"]:
                nuevo = _a_bool(nuevo)
            else:
                if isinstance(nuevo, str) and " - " in nuevo:
                    nuevo = nuevo.split(" - ", 1)[0].strip()
                nuevo = int(nuevo)
            res = getattr(crud, cfg["metodo_estado"])(pk, nuevo)
        elif accion == "eliminar":
            sig = inspect.signature(crud.eliminar)
            if "baja_logica" in sig.parameters:
                res = crud.eliminar(pk, baja_logica=False)
            else:
                res = crud.eliminar(pk)
        elif accion == "siguiente_id":
            if modulo != "personal":
                return {"estado": False, "mensaje": "Solo disponible en personal"}
            res = {"estado": True, "siguiente_id": crud.obtener_siguiente_id()}
        else:
            res = {"estado": False, "mensaje": "Acción no válida"}

        return _estado_a_texto(res, cfg)
    finally:
        cnn.cerrar_conexion()


# ---------------------------------------------------------------------------
# Vistas de Plantillas HTML
# ---------------------------------------------------------------------------
def index(request):
    """Menú principal como vista predeterminada del sistema."""
    return render(request, "menu_principal.html")


def menu_principal(request):
    return render(request, "menu_principal.html")


def catalogos(request):
    return render(request, "catalogos.html")


def gestion_grupos(request):
    return render(request, "Gestion_de_grupos.html")


def programacion_grupos(request):
    return render(request, "Programacion_De_Grupos.html")


def inscripciones(request):
    return render(request, "Inscripciones.html")


def pagos_caja(request):
    return render(request, "Pagos_y_Caja.html")


def evaluacion_kardex(request):
    return render(request, "Evaluacion_y_kardex.html")


def seguridad_usuarios(request):
    return render(request, "Seguridad_y_Usuarios.html")


def login_view(request):
    return render(request, "login.html")


def legacy_index(request):
    return render(request, "index.html")


@require_http_methods(["GET", "POST"])
def api(request, modulo, accion, pk=None):
    if modulo not in MODULOS:
        return JsonResponse({"estado": False, "mensaje": "Módulo no existe"}, status=404)

    if (accion in ACCIONES_POST) != (request.method == "POST"):
        return JsonResponse({"estado": False, "mensaje": "Método HTTP no permitido"}, status=405)

    datos = {}
    if request.method == "POST" and request.body:
        try:
            datos = json.loads(request.body)
        except ValueError:
            return JsonResponse({"estado": False, "mensaje": "JSON inválido"}, status=400)

    try:
        res = _llamar(modulo, accion, pk, datos)
    except Exception as e:  # cualquier error inesperado se devuelve como JSON
        res = {"estado": False, "mensaje": "Error inesperado", "error": str(e)}

    return JsonResponse(res, encoder=DjangoJSONEncoder, json_dumps_params={"ensure_ascii": False})
