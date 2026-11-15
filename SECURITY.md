# Política de Seguridad

Haydeén Sistema gestiona información clínica y administrativa. Tratamos los reportes de seguridad con prioridad y agradecemos la divulgación responsable.

> **Aviso:** este documento describe el proceso de reporte y las prácticas esperadas. No constituye asesoría legal ni certifica el cumplimiento de HIPAA, GDPR, LFPDPPP, NOM-004-SSA3 u otra normativa. Cada despliegue debe realizar su propio análisis de riesgos y cumplimiento.

## Versiones soportadas

| Versión | Estado | Soporte de seguridad |
| --- | --- | --- |
| `0.1.x` | MVP funcional | Sí, mientras sea la versión publicada más reciente |
| `< 0.1.0` | Desarrollo interno | No |

El proyecto sigue versionado semántico (`MAJOR.MINOR.PATCH`). Las correcciones de seguridad se publican en la rama `main` y, cuando aplique, en una rama de mantenimiento con backport.

## Reportar una vulnerabilidad

**No abras un issue público, un pull request ni una discusión con detalles de la vulnerabilidad.**

Usa uno de estos canales privados:

1. **GitHub Security Advisories** (preferido):
   `https://github.com/<OWNER>/<REPO>/security/advisories/new`
2. **Correo de seguridad:**
   `security@example.com`

> Reemplaza `<OWNER>`, `<REPO>` y `security@example.com` por los datos reales antes de publicar el repositorio.

### Qué incluir en el reporte

- Descripción clara de la vulnerabilidad y su impacto.
- Componente afectado: `api`, `desktop`, `web`, `database` o `scripts`.
- Versión o commit afectado.
- Entorno: sistema operativo, versión de Python, MySQL y navegador.
- Pasos de reproducción detallados.
- Prueba de concepto (PoC) mínima, si es posible.
- Impacto estimado: confidencialidad, integridad, disponibilidad o seguridad clínica.
- Mitigación o parche sugerido, si lo tienes.
- Si deseas reconocimiento público, indica el nombre o alias.

No incluyas datos reales de pacientes, credenciales de producción ni información de terceros. Usa datos sintéticos.

### Cifrado de comunicaciones

Si el reporte contiene información sensible, solicita una clave pública PGP en el correo de seguridad antes de enviar el detalle. También puedes usar el canal privado de GitHub Security Advisories.

## Proceso de respuesta

| Etapa | Objetivo | Plazo orientativo |
| --- | --- | --- |
| Acuse de recibo | Confirmar que el reporte fue recibido | 48 horas hábiles |
| Triaje | Clasificar severidad e impacto | 5 días hábiles |
| Contención | Mitigación temporal o workaround | 7 días hábiles para críticas |
| Corrección | Parche y pruebas | 30 días para críticas; 90 días para el resto |
| Divulgación coordinada | Aviso público y créditos | Después del parche o a los 90 días |

Los plazos son orientativos y pueden variar según la complejidad. Mantendremos informado al reportero durante el proceso.

### Severidad

| Nivel | Ejemplos |
| --- | --- |
| **Crítica** | Ejecución remota de código, bypass de autenticación, acceso masivo a datos de pacientes, inyección SQL explotable |
| **Alta** | Escalada de privilegios, robo de sesión, exposición de credenciales, IDOR sobre datos clínicos |
| **Media** | XSS almacenado, CSRF, divulgación limitada de información, denegación de servicio acotada |
| **Baja** | Divulgación menor, errores de configuración sin impacto directo, mejoras de endurecimiento |

## Alcance

### En alcance

- API FastAPI: autenticación, sesiones, validación, autorización y endpoints.
- Panel de escritorio CustomTkinter y su cliente HTTP.
- App móvil: manejo de tokens, XSS, almacenamiento local y lógica de UI.
- Esquema SQL, consultas, permisos y migraciones.
- Scripts de PowerShell de importación y arranque.
- Configuración de ejemplo y documentación de despliegue.

### Fuera de alcance

- Vulnerabilidades en dependencias de terceros sin impacto demostrable en el proyecto (repórtalas también al proveedor).
- Ingeniería social, phishing o ataques físicos.
- Denegación de servicio por fuerza bruta o volumétrica sin una debilidad concreta.
- Reportes generados automáticamente sin reproducción ni impacto demostrable.
- Entornos de demostración con datos sintéticos donde no exista información real de pacientes.
- Falta de cabeceras de seguridad en un servidor de desarrollo local.

## Puerto seguro (safe harbor)

Si actúas de buena fe, respetas la privacidad, no accedes a datos de pacientes reales, no degradas el servicio y nos das un plazo razonable para corregir, no iniciaremos acciones legales por tu investigación. Esta declaración no autoriza pruebas sobre sistemas de terceros ni sobre datos reales.

## Prácticas de despliegue seguro

Antes de usar el sistema con datos reales:

1. **Rota las contraseñas del seeder.** `seed_system.py --apply` genera claves aleatorias; cámbialas antes de usar datos reales con `--reset-passwords`.
2. **Revisa la matriz de permisos** en `rol_permisos` y asigna a cada persona el rol mínimo necesario.
3. **Usa un usuario MySQL dedicado**, no `root`, con permisos mínimos sobre `haydeensistem`.
4. **Configura `CORS_ORIGINS`** con los orígenes reales; no uses `*`.
5. **Define `SECRET_KEY`** y no la compartas; cambiarla invalida todas las sesiones.
6. **Sirve la API detrás de HTTPS** con Caddy, Nginx o Traefik. No expongas HTTP a Internet.
7. **Restringe el firewall** a la LAN o a la VPN. No publiques el puerto 8000.
8. **Activa respaldos cifrados** y prueba la restauración.
9. **Rota sesiones y contraseñas** si sospechas una exposición.
10. **Revisa logs** sin incluir datos clínicos, tokens ni contraseñas.
11. **Mantén dependencias actualizadas** y ejecuta auditorías (`pip-audit`).
10. **Realiza validación clínica y análisis de riesgos** antes de usar el sistema en decisiones de atención.

Consulta la lista completa en [`SECURITY_CHECKLIST.md`](SECURITY_CHECKLIST.md).

## Brechas de seguridad

Si detectas o sospechas una brecha:

1. Contén el servicio si es necesario.
2. Revoca sesiones (`DELETE FROM sesiones;`) y rota credenciales.
3. Conserva evidencia y logs.
4. Notifica al responsable de privacidad y a las autoridades si la normativa lo exige.
5. Documenta el incidente, el impacto y las acciones correctivas.

## Seguridad clínica

Un fallo de seguridad puede convertirse en un riesgo clínico. Si detectas un problema que pueda afectar la administración de medicamentos, la identificación de pacientes o la integridad de los registros:

- Repórtalo por el canal privado con la etiqueta **seguridad clínica**.
- Incluye el flujo afectado y el posible daño al paciente.
- No esperes a la divulgación pública para solicitar contención.

## Dependencias y terceros

El proyecto usa FastAPI, Uvicorn, PyMySQL, python-dotenv, cryptography, CustomTkinter, Requests, Pillow y Tailwind CSS por CDN. Las vulnerabilidades en estos componentes deben reportarse también a sus mantenedores. Si el impacto en Haydeén Sistema es demostrable, inclúyelo en tu reporte.

## Reconocimientos

Agradecemos a las personas que reportan vulnerabilidades de forma responsable. Con tu permiso, podemos incluir tu nombre o alias en las notas de la versión corregida.

## Sin garantía

Este proyecto se distribuye bajo la **MIT License**. Se proporciona **tal cual**, sin garantías de ningún tipo. Consulta [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE). La licencia no sustituye las obligaciones sanitarias ni la responsabilidad por negligencia.
