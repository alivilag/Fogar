import os
import re
import streamlit as st

index_path = os.path.join(os.path.dirname(st.__file__), "static", "index.html")

pwa_tags = """
<link rel="manifest" href="/app/static/assets/manifest.json">
<link rel="shortcut icon" href="/app/static/assets/icon-192.png">
<link rel="apple-touch-icon" href="/app/static/assets/icon-192.png">
<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/app/static/sw.js').catch(function(err) {
                console.log('Error SW:', err);
            });
        });
    }
</script>
"""

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

# Eliminar iconos por defecto de Streamlit
html = re.sub(r'<link rel="shortcut icon"[^>]*>', '', html)
html = re.sub(r'<link rel="apple-touch-icon"[^>]*>', '', html)

# Inyectar configuración PWA
if 'rel="manifest"' not in html:
    html = html.replace("</head>", f"{pwa_tags}\n</head>")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
