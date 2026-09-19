# Verificación

## Comprobador
Desde la raíz, con Git Bash: bash ./init.sh.
Con las dependencias YAML, activar primero el entorno. Desde PowerShell: `.\venv\Scripts\Activate.ps1`.
En este equipo invocar Git Bash explícitamente: `& 'C:\Program Files\Git\bin\bash.exe' ./init.sh` (el bash del PATH puede corresponder a WSL).
Instalación desde PowerShell: `venv/Scripts/python.exe -m pip install -r requirements.txt`.
Comprueba Python disponible, archivos base, estados del listado de tareas y ejecuta unittest si encuentra pruebas.
Que termine correctamente no demuestra por sí solo que una función cumpla sus requisitos.
Selecciona Python del PATH: hay que activar venv antes de ejecutarlo. El script no activa el entorno automáticamente.

Comprobación manual: `venv/Scripts/python.exe src/small_cli.py download`.
Esto crea y elimina una sonda temporal en data_dir para verificar escritura. No descarga datos.

## Evidencia por tarea
- Comprobar los criterios de aceptación de la especificación aprobada.
- Para código, usar pruebas que verifiquen resultados y errores relevantes.
- Para documentación, revisar coherencia, referencias y alcance; no crear pruebas artificiales.
- Ejecutar el comprobador antes de editar y antes de cerrar.
- Registrar resultado y limitaciones en el change de openspec/ o en progress/history.md para tareas pequeñas.
- No marcar done si falla una comprobación requerida.
- Una revisión sin modificaciones no necesita abrir una tarea ni editar el registro de progreso.

La lista breve de cierre está en las reglas de openspec/config.yaml.
