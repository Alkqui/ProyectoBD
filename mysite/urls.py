from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Página principal predeterminada (menu_principal.html)
    path("", views.index, name="index"),
    path("menu_principal.html", views.menu_principal, name="menu_principal_html"),
    path("menu_principal/", views.menu_principal, name="menu_principal"),

    # Vistas de los módulos del menú principal
    path("catalogos.html", views.catalogos, name="catalogos_html"),
    path("catalogos/", views.catalogos, name="catalogos"),
    path("Gestion_de_grupos.html", views.gestion_grupos, name="gestion_grupos_html"),
    path("aspirantes/", views.gestion_grupos, name="gestion_grupos"),
    path("Programacion_De_Grupos.html", views.programacion_grupos, name="programacion_grupos_html"),
    path("programacion/", views.programacion_grupos, name="programacion_grupos"),
    path("Inscripciones.html", views.inscripciones, name="inscripciones_html"),
    path("inscripciones/", views.inscripciones, name="inscripciones"),
    path("Pagos_y_Caja.html", views.pagos_caja, name="pagos_caja_html"),
    path("pagos/", views.pagos_caja, name="pagos_caja"),
    path("Evaluacion_y_kardex.html", views.evaluacion_kardex, name="evaluacion_kardex_html"),
    path("evaluacion/", views.evaluacion_kardex, name="evaluacion_kardex"),
    path("Seguridad_y_Usuarios.html", views.seguridad_usuarios, name="seguridad_usuarios_html"),
    path("seguridad/", views.seguridad_usuarios, name="seguridad_usuarios"),
    path("login.html", views.login_view, name="login_html"),
    path("login/", views.login_view, name="login"),
    path("index.html", views.legacy_index, name="legacy_index"),

    # API JSON (la consumen los archivos HTML de templates/)
    path("api/<str:modulo>/", views.api, {"accion": "listar"}),
    path("api/<str:modulo>/crear/", views.api, {"accion": "crear"}),
    path("api/<str:modulo>/siguiente-id/", views.api, {"accion": "siguiente_id"}),
    path("api/<str:modulo>/<int:pk>/", views.api, {"accion": "detalle"}),
    path("api/<str:modulo>/<int:pk>/actualizar/", views.api, {"accion": "actualizar"}),
    path("api/<str:modulo>/<int:pk>/estado/", views.api, {"accion": "estado"}),
    path("api/<str:modulo>/<int:pk>/eliminar/", views.api, {"accion": "eliminar"}),
]
