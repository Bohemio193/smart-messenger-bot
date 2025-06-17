# Smart Messenger Bot para Render

## 🚀 Bot de Telegram con programación de mensajes

### Características principales:
- ✅ Reconexión automática
- ✅ Persistencia de datos
- ✅ Programación de mensajes con formato simple
- ✅ Monitoreo 24/7
- ✅ Compatible con Render

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

## 📋 Instrucciones de deployment en Render:

### 1. Crear nuevo Web Service en Render:
   - Conecta tu repositorio GitHub
   - Selecciona "Web Service"
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

### 2. Configurar variables de entorno:
   - `TELEGRAM_BOT_TOKEN` = Tu token de BotFather

### 3. Deploy:
   - Render detectará automáticamente los archivos
   - El bot se iniciará y estará disponible 24/7

## 🔧 Características técnicas:

### Reconexión automática:
- El bot se reinicia automáticamente si se desconecta
- Manejo robusto de errores de red
- Logging detallado para diagnóstico

### Persistencia:
- Los mensajes programados se guardan en archivo JSON
- Supervive reinicios y deployment
- Verificación cada 30 segundos

### Monitoreo:
- Endpoint HTTP para verificar estado
- Estadísticas de uso en tiempo real
- Logs detallados de operaciones

## 📱 Uso del bot:

### Programar mensajes:
```
/programar 30m Tomar medicamento
/programar 2h Llamar al cliente
/programar 1d Reunión importante
```

### Ver mensajes programados:
```
/mensajes
```

### Cancelar mensaje:
```
/cancelar 1718234567890
```

### Ver estado del bot:
```
/estado
```

## 🚨 Resolución de problemas:

### Si el bot no responde:
1. Verificar que `TELEGRAM_BOT_TOKEN` esté configurado
2. Revisar logs en Render dashboard
3. El bot se reinicia automáticamente cada 10 segundos si falla

### Si los mensajes no se envían:
1. Verificar que el formato de tiempo sea correcto
2. Usar `/estado` para ver estadísticas
3. Los mensajes se verifican cada 30 segundos

## 💡 Soporte:
- Bot robusto con manejo de errores
- Reconexión automática garantizada
- Compatible con plan gratuito de Render
