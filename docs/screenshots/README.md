# Capturas de pantalla

Las imágenes de esta carpeta son **placeholders SVG editables**. Sirven para que el README se vea completo desde el primer commit y para evitar imágenes rotas.

| Archivo | Vista | Uso |
| --- | --- | --- |
| `desktop-dashboard.svg` | Panel de escritorio · Dashboard | Totales y próximas administraciones |
| `desktop-pacientes.svg` | Panel de escritorio · Pacientes | Tabla de residentes |
| `mobile-pacientes.svg` | App móvil · Pacientes | Listado y búsqueda |
| `mobile-control.svg` | App móvil · Control diario | Signos vitales del turno |
| `mobile-administracion.svg` | App móvil · Administración | Registro de dosis y lote |
| `mobile-signos.svg` | App móvil · Modal de signos | Formulario de captura |

## Reemplazar por capturas reales

1. Usa **datos sintéticos**. Nunca captures nombres, documentos, diagnósticos ni teléfonos reales.
2. Oculta o difumina la barra de tareas, notificaciones y cualquier dato del sistema operativo.
3. Guarda las imágenes con el mismo nombre base (`desktop-dashboard.png`, etc.).
4. Si cambias de extensión, actualiza las rutas en `README.md`.
5. Optimiza el peso: PNG para UI, WebP si el navegador objetivo lo soporta. Menos de 500 KB por imagen.

Sugerencia de resolución:

- Escritorio: 1440×900 o 1280×800, ventana maximizada.
- Móvil: 390×844 (iPhone 12/13/14) o 360×800 (Android común), sin marco del dispositivo.

## Regenerar los placeholders

Los SVG son texto plano. Puedes editarlos con cualquier editor y ajustar nombres, colores o textos. Mantén:

- `role="img"` y `aria-labelledby` para accesibilidad.
- Un `<title>` y un `<desc>` descriptivos.
- Textos en español y la nota «Captura ilustrativa · datos sintéticos».

## Aviso

Estas maquetas **no representan una validación clínica** ni el estado exacto de la interfaz. Son ilustraciones de referencia para documentación.
