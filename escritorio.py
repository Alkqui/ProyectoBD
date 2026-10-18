
import argparse
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
load_dotenv(BASE / ".env")

from mysite.views import MODULOS, _llamar  # noqa: E402  (misma lógica que la web)

CARPETA_TEMPLATES = BASE / "mysite" / "templates"
HTML_ORIGINAL = CARPETA_TEMPLATES / "menu_principal.html"
RECURSOS = BASE / "recursos"

# Scripts que el HTML carga de internet -> archivos locales en ./recursos
CDN_A_LOCAL = {
    '<script src="https://cdn.tailwindcss.com"></script>': "tailwind.js",
    '<script src="https://unpkg.com/lucide@latest"></script>': "lucide.min.js",
}

ACCIONES_POST = {"crear", "actualizar", "estado", "eliminar"}
ACCIONES_GET = {"listar", "detalle", "siguiente_id"}


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def preparar_html(ruta_archivo=None):
    """Lee un archivo HTML de templates/, quita lo propio de Django y usa recursos locales."""
    objetivo = ruta_archivo or HTML_ORIGINAL
    html = objetivo.read_text(encoding="utf-8")
    html = html.replace("{{ csrf_token }}", "")  # aquí no hay CSRF (solo local)
    faltantes = []
    for etiqueta, archivo in CDN_A_LOCAL.items():
        if (RECURSOS / archivo).exists():
            html = html.replace(etiqueta, f'<script src="/recursos/{archivo}"></script>')
        else:
            faltantes.append(archivo)
    return html, faltantes


# ---------------------------------------------------------------------------
# Mini servidor local
# ---------------------------------------------------------------------------
class Manejador(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):
        print(f"[web] {self.command} {self.path}")

    def _enviar(self, codigo, cuerpo, tipo):
        datos = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def _json(self, res, codigo=200):
        texto = json.dumps(res, ensure_ascii=False, default=str)
        self._enviar(codigo, texto, "application/json; charset=utf-8")

    def do_GET(self):
        self._despachar("GET")

    def do_POST(self):
        self._despachar("POST")

    def _despachar(self, metodo):
        ruta = self.path.split("?")[0]
        partes = [p for p in ruta.split("/") if p]

        if metodo == "GET" and ruta == "/":
            html, _ = preparar_html(HTML_ORIGINAL)
            return self._enviar(200, html, "text/html; charset=utf-8")

        if metodo == "GET" and len(partes) == 1 and partes[0].endswith(".html"):
            archivo_tpl = CARPETA_TEMPLATES / Path(partes[0]).name
            if archivo_tpl.is_file():
                html, _ = preparar_html(archivo_tpl)
                return self._enviar(200, html, "text/html; charset=utf-8")

        if metodo == "GET" and partes[:1] == ["recursos"] and len(partes) == 2:
            archivo = RECURSOS / Path(partes[1]).name  # evita salirse de la carpeta
            if archivo.is_file():
                return self._enviar(200, archivo.read_bytes(), "application/javascript")
            return self._enviar(404, "No encontrado", "text/plain")

        if partes[:1] == ["api"] and len(partes) >= 2:
            return self._api(metodo, partes[1], partes[2:])

        self._enviar(404, "No encontrado", "text/plain")

    def _api(self, metodo, modulo, resto):
        if modulo not in MODULOS:
            return self._json({"estado": False, "mensaje": "Módulo no existe"}, 404)

        pk = None
        if not resto:
            accion = "listar"
        elif resto == ["crear"]:
            accion = "crear"
        elif resto == ["siguiente-id"]:
            accion = "siguiente_id"
        elif resto[0].isdigit() and len(resto) <= 2:
            pk = int(resto[0])
            accion = "detalle" if len(resto) == 1 else resto[1]
        else:
            return self._json({"estado": False, "mensaje": "Ruta no válida"}, 404)

        if accion not in ACCIONES_POST | ACCIONES_GET:
            return self._json({"estado": False, "mensaje": "Acción no válida"}, 404)
        if (accion in ACCIONES_POST) != (metodo == "POST"):
            return self._json({"estado": False, "mensaje": "Método HTTP no permitido"}, 405)

        datos = {}
        if metodo == "POST":
            largo = int(self.headers.get("Content-Length") or 0)
            if largo:
                try:
                    datos = json.loads(self.rfile.read(largo))
                except ValueError:
                    return self._json({"estado": False, "mensaje": "JSON inválido"}, 400)

        try:
            res = _llamar(modulo, accion, pk, datos)
        except Exception as e:
            res = {"estado": False, "mensaje": "Error inesperado", "error": str(e)}
        self._json(res)


def iniciar_servidor():
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)  # puerto libre
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


# ---------------------------------------------------------------------------
# Ventana Qt6
# ---------------------------------------------------------------------------
def abrir_ventana(url, motor):
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QAction, QKeySequence
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWidgets import QApplication, QMainWindow
    except ImportError:
        sys.exit("Falta PySide6. Instálalo con:  pip install PySide6")

    class Ventana(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"Centro de Idiomas - Gestión  [{motor}]")
            self.resize(1280, 800)

            self.vista = QWebEngineView(self)
            self.vista.load(QUrl(url))
            self.setCentralWidget(self.vista)

            menu_archivo = self.menuBar().addMenu("&Archivo")
            salir = QAction("Salir", self)
            salir.setShortcut(QKeySequence("Ctrl+Q"))
            salir.triggered.connect(self.close)
            menu_archivo.addAction(salir)

            menu_ver = self.menuBar().addMenu("&Ver")
            recargar = QAction("Recargar", self)
            recargar.setShortcut(QKeySequence("F5"))
            recargar.triggered.connect(self.vista.reload)
            menu_ver.addAction(recargar)

    app = QApplication([sys.argv[0]])
    ventana = Ventana()
    ventana.show()
    return app.exec()


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Interfaz de escritorio - Centro de Idiomas")
    parser.add_argument("--motor", choices=["postgresql", "sqlserver"],
                        help="Motor de BD (por defecto el MOTOR_BD del .env)")
    args = parser.parse_args()

    if args.motor:
        os.environ["MOTOR_BD"] = args.motor
    motor = os.environ.get("MOTOR_BD", "postgresql").lower()

    if not HTML_ORIGINAL.exists():
        sys.exit(f"No se encontró {HTML_ORIGINAL}")

    _, faltantes = preparar_html()
    if faltantes:
        print("AVISO: faltan recursos locales:", ", ".join(faltantes))
        print("       Sin ellos la página necesita internet. Ejecuta: python descargar_recursos.py\n")

    servidor = iniciar_servidor()
    url = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print(f"Motor de BD : {motor}")
    print(f"Servidor    : {url}  (solo local)")
    print("Cierra la ventana para terminar.\n")

    codigo = abrir_ventana(url, motor)
    servidor.shutdown()
    sys.exit(codigo)


if __name__ == "__main__":
    main()
