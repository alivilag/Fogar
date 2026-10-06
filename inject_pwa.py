import os
import streamlit as st

# Localizar el archivo base index.html de la librería Streamlit
index_path = os.path.join(os.path.dirname(st.__file__), "static", "index.html")

pwa_tags = """
<link rel="manifest" href="/app/static/assets/manifest.json">
<link rel="shortcut icon" href="/app/static/assets/icon-192.png">
<link rel="apple-touch-icon" href="/app/static/assets/icon-192.png">
"""

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Inyectar las etiquetas PWA justo antes de cerrar el <head>
if "rel=\"manifest\"" not in html:
    html = html.replace("</head>", f"{pwa_tags}\n</head>")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
