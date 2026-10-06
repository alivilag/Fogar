import os
import re
import shutil
import streamlit as st

# 1. Encontrar la carpeta núcleo de Streamlit
st_dir = os.path.dirname(st.__file__)
st_static_dir = os.path.join(st_dir, "static")
index_path = os.path.join(st_static_dir, "index.html")

# 2. Copiar tus archivos a la raíz del servidor interno de Streamlit
shutil.copy("static/manifest.json", st_static_dir)
shutil.copy("icon-192.png", st_static_dir)
shutil.copy("icon-512.png", st_static_dir)
shutil.copy("static/sw.js", st_static_dir)

# 3. Etiquetas limpias apuntando a la raíz absoluta (/)
pwa_tags = """
<link rel="manifest" href="/manifest.json">
<link rel="shortcut icon" href="/icon-192.png">
<link rel="apple-touch-icon" href="/icon-192.png">
<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/sw.js');
        });
    }
</script>
"""

# 4. Leer, limpiar iconos por defecto e inyectar
with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

html = re.sub(r'<link rel="shortcut icon"[^>]*>', '', html)
html = re.sub(r'<link rel="apple-touch-icon"[^>]*>', '', html)

if 'rel="manifest"' not in html:
    html = html.replace("</head>", f"{pwa_tags}\n</head>")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
