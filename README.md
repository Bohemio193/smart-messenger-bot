# Smart Messenger Bot CORREGIDO para Render

## ✅ SOLUCIONADO: Error imghdr en Python 3.13

### Cambios realizados:
- ✅ Python 3.11 en lugar de 3.13 (runtime.txt)
- ✅ Agregado Pillow para compatibilidad de imágenes
- ✅ Versión específica de python-telegram-bot
- ✅ Reconexión automática garantizada

## 🚀 Bot de Telegram con programación de mensajes

### Comandos disponibles:
- `/start` - Mensaje de bienvenida
- `/programar 5m Recordatorio` - Programa mensaje en 5 minutos
- `/programar 2h Reunión` - Programa mensaje en 2 horas  
- `/programar 1d Evento` - Programa mensaje en 1 día
- `/mensajes` - Ver todos los mensajes programados
- `/cancelar <ID>` - Cancelar mensaje específico
- `/estado` - Ver estadísticas del bot
- `/ayuda` - Ver ayuda completa

### Formatos de tiempo soportados:
- `5m` = 5 minutos
- `2h` = 2 horas
- `1d` = 1 día
- `3w` = 3 semanas

## 📋 Instrucciones de deployment:

### OPCIÓN 1: Actualizar repositorio existente
1. Reemplaza todos los archivos en tu repositorio GitHub
2. Hacer commit y push
3. Render detectará automáticamente los cambios
4. Redeploy automático

### OPCIÓN 2: Nuevo repositorio
1. Crear nuevo repositorio GitHub
2. Subir estos archivos corregidos
3. Crear nuevo Web Service en Render
4. Configurar TELEGRAM_BOT_TOKEN

## 🔧 Configuración Render:
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`
- Environment Variable: `TELEGRAM_BOT_TOKEN`

## ✨ Funcionará sin errores en Render
