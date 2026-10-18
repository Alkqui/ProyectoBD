Para ejecutar la app de escritorio solo hace falta ejecutar escritorio.py
Para ejecutar la app web solo escribe este comando dentro del entorno virtual:
python manage.py runserver

El proyecto utiliza las librerías **PySide6 y Qt WebEngine** para convertir la interfaz web desarrollada con HTML, CSS y JavaScript en una aplicación de escritorio. PySide6 permite crear la ventana de la aplicación, mientras que Qt WebEngine incorpora un motor basado en Chromium que interpreta y muestra el contenido web dentro de dicha ventana. De esta manera, es posible aprovechar la interfaz web existente sin tener que desarrollarla nuevamente desde cero para un entorno de escritorio.
