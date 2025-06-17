# Smart Messenger Bot v3.0 - Enhanced

## 🌟 NUEVAS FUNCIONALIDADES

### Programación Avanzada:
- ✅ Horarios específicos: `14:30`, `09:00`
- ✅ Fechas específicas: `2024-12-25 14:30`
- ✅ Formatos tradicionales: `5m`, `2h`, `1d`
- ✅ Segundos para testing: `30s`

### Consulta del Clima:
- ✅ Clima en tiempo real con OpenWeatherMap
- ✅ Ubicaciones guardadas por usuario
- ✅ Iconos y formato mejorado
- ✅ Datos en español

### Comandos Mejorados:
- `/programar 14:30 Reunión` - Horario específico
- `/clima La Habana` - Clima de cualquier ciudad
- `/ubicacion Madrid` - Guardar ubicación
- `/clima` - Clima de ubicación guardada
- `/mensajes` - Ver con tiempo restante
- `/estado` - Estadísticas completas

## 📋 Variables de Entorno Necesarias:

### Obligatoria:
- `TELEGRAM_BOT_TOKEN` - Token del bot de Telegram

### Opcional (para clima):
- `OPENWEATHER_API_KEY` - API key de OpenWeatherMap
  - Obtener gratis en: https://openweathermap.org/api
  - Sin esta API, las funciones del clima no funcionarán

## 🚀 Deployment en Render:

1. **Configurar variables de entorno:**
   - `TELEGRAM_BOT_TOKEN` = Tu token de BotFather
   - `OPENWEATHER_API_KEY` = Tu API key del clima (opcional)

2. **El bot funcionará sin API del clima**, solo mostrará mensaje de no configurada

3. **Build automático** con las dependencias mínimas

## ✨ Características Técnicas:

### Persistencia Mejorada:
- Datos en `bot_data.json`
- Ubicaciones de usuarios guardadas
- Mensajes programados persistentes

### Programación Inteligente:
- Parser avanzado de tiempo
- Validación de fechas pasadas
- Cálculo de tiempo restante
- Formatos múltiples soportados

### API del Clima:
- Datos en tiempo real
- Iconos meteorológicos
- Información completa (temp, humedad, sensación)
- Manejo de errores de API

### Sin errores garantizado en Render
