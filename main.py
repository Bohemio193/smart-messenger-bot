#!/usr/bin/env python3
import os
import json
import logging
import time
import requests
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, jsonify

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

scheduled_messages = []
user_locations = {}  # Guardar ubicaciones de usuarios
bot_stats = {
    'messages_sent': 0,
    'commands_received': 0,
    'weather_requests': 0,
    'uptime_start': datetime.now(),
    'restarts_count': 0
}

def load_data():
    global scheduled_messages, user_locations
    try:
        if os.path.exists('bot_data.json'):
            with open('bot_data.json', 'r') as f:
                data = json.load(f)
                scheduled_messages = data.get('messages', [])
                user_locations = data.get('locations', {})
                logger.info(f"Datos cargados: {len(scheduled_messages)} mensajes, {len(user_locations)} ubicaciones")
    except Exception as e:
        logger.error(f"Error cargando datos: {e}")
        scheduled_messages = []
        user_locations = {}

def save_data():
    try:
        data = {
            'messages': scheduled_messages,
            'locations': user_locations,
            'last_updated': datetime.now().isoformat()
        }
        with open('bot_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error guardando datos: {e}")

def send_telegram_message(chat_id, text, reply_markup=None):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        data = {
            'chat_id': chat_id, 
            'text': text, 
            'parse_mode': 'Markdown'
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data, timeout=30)
        return response.json().get('ok', False)
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return False

def get_telegram_updates(offset=0):
    try:
        url = f"{TELEGRAM_API}/getUpdates"
        params = {'offset': offset, 'timeout': 30}
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo updates: {e}")
        return {'ok': False, 'result': []}

def get_weather_data(city):
    """Obtener datos del clima usando OpenWeatherMap"""
    if not OPENWEATHER_API_KEY:
        return None
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'es'
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error API clima: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error obteniendo clima: {e}")
        return None

def format_weather_message(weather_data, city):
    """Formatear mensaje del clima"""
    try:
        temp = round(weather_data['main']['temp'])
        feels_like = round(weather_data['main']['feels_like'])
        humidity = weather_data['main']['humidity']
        description = weather_data['weather'][0]['description'].title()
        
        # Iconos del clima
        weather_icons = {
            'clear sky': '☀️',
            'few clouds': '🌤️',
            'scattered clouds': '⛅',
            'broken clouds': '☁️',
            'shower rain': '🌦️',
            'rain': '🌧️',
            'thunderstorm': '⛈️',
            'snow': '❄️',
            'mist': '🌫️'
        }
        
        icon = weather_icons.get(weather_data['weather'][0]['description'], '🌡️')
        
        message = f"""🌤️ *Clima en {city.title()}*

{icon} *{description}*
🌡️ *Temperatura:* {temp}°C
🤚 *Sensación térmica:* {feels_like}°C
💧 *Humedad:* {humidity}%

_Datos actualizados hace pocos minutos_"""
        
        return message
    except Exception as e:
        logger.error(f"Error formateando clima: {e}")
        return f"Error procesando datos del clima para {city}"

def parse_time_advanced(time_str):
    """Parser avanzado de tiempo con más opciones"""
    try:
        # Formatos básicos: 5m, 2h, 1d
        if time_str[-1] == 'm':
            minutes = int(time_str[:-1])
            return datetime.now() + timedelta(minutes=minutes)
        elif time_str[-1] == 'h':
            hours = int(time_str[:-1])
            return datetime.now() + timedelta(hours=hours)
        elif time_str[-1] == 'd':
            days = int(time_str[:-1])
            return datetime.now() + timedelta(days=days)
        elif time_str[-1] == 's':
            seconds = int(time_str[:-1])
            return datetime.now() + timedelta(seconds=seconds)
        
        # Formato hora específica: 14:30, 09:15
        if ':' in time_str:
            try:
                hour, minute = map(int, time_str.split(':'))
                now = datetime.now()
                scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Si la hora ya pasó hoy, programar para mañana
                if scheduled <= now:
                    scheduled += timedelta(days=1)
                
                return scheduled
            except:
                pass
        
        # Formato fecha y hora: 2024-12-25 14:30
        if ' ' in time_str and ':' in time_str:
            try:
                date_part, time_part = time_str.split(' ')
                year, month, day = map(int, date_part.split('-'))
                hour, minute = map(int, time_part.split(':'))
                return datetime(year, month, day, hour, minute)
            except:
                pass
                
    except:
        pass
    return None

def create_time_examples_keyboard():
    """Crear teclado con ejemplos de horarios"""
    return {
        'keyboard': [
            ['⏰ 5m - 5 minutos', '⏰ 1h - 1 hora'],
            ['⏰ 2h - 2 horas', '⏰ 1d - 1 día'],
            ['⏰ 14:30 - Hoy 2:30 PM', '⏰ 09:00 - Mañana 9:00 AM'],
            ['📍 Mi ubicación', '🌤️ Clima actual'],
            ['❌ Cancelar']
        ],
        'resize_keyboard': True,
        'one_time_keyboard': True
    }

def handle_command(message):
    global bot_stats, scheduled_messages, user_locations
    
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_name = message['from'].get('first_name', 'Usuario')
    user_id = str(message['from']['id'])
    
    bot_stats['commands_received'] += 1
    
    if text == '/start':
        welcome = f"""¡Hola {user_name}! 👋

🤖 *Smart Messenger Bot v3.0*
_Bot inteligente con clima y programación avanzada_

🚀 *Nuevas funcionalidades:*
• Programación avanzada de mensajes
• Consulta del clima en tiempo real
• Horarios específicos (14:30, 09:00)
• Ubicaciones guardadas
• Recordatorios inteligentes

📋 *Comandos principales:*
/programar - Programar mensaje avanzado
/clima - Consultar clima
/ubicacion - Guardar mi ubicación
/mensajes - Ver programados
/estado - Estado del bot
/ayuda - Ayuda completa

¡Prueba /clima La Habana o /programar!"""
        
        send_telegram_message(chat_id, welcome)
    
    elif text == '/ayuda' or text == '/help':
        help_text = """🤖 *Smart Messenger Bot v3.0 - Ayuda*

📋 *Comandos principales:*

🔸 `/programar <tiempo> <mensaje>`
   *Formatos de tiempo:*
   • `5m` = 5 minutos
   • `2h` = 2 horas
   • `1d` = 1 día
   • `14:30` = Hoy a las 2:30 PM
   • `09:00` = Mañana a las 9:00 AM

🔸 `/clima <ciudad>` - Clima actual
   • `/clima La Habana`
   • `/clima Miami`
   • `/clima` (usa ubicación guardada)

🔸 `/ubicacion <ciudad>` - Guardar ubicación
   • `/ubicacion La Habana`

🔸 `/mensajes` - Ver mensajes programados
🔸 `/cancelar <ID>` - Cancelar mensaje
🔸 `/estado` - Estadísticas del bot

💡 *Ejemplos prácticos:*
```
/programar 30m Tomar medicina
/programar 14:30 Reunión importante
/programar 1d Evento mañana
/clima
/ubicacion Madrid
```

🌟 *Funciones especiales:*
• Recordatorios con horario específico
• Clima automático de tu ubicación
• Programación hasta días específicos"""
        
        send_telegram_message(chat_id, help_text)
    
    elif text.startswith('/clima'):
        bot_stats['weather_requests'] += 1
        parts = text.split(' ', 1)
        
        if len(parts) > 1:
            city = parts[1]
        elif user_id in user_locations:
            city = user_locations[user_id]
        else:
            send_telegram_message(chat_id, 
                "❌ Especifica una ciudad: `/clima La Habana`\n\n"
                "O guarda tu ubicación: `/ubicacion Tu_Ciudad`")
            return
        
        weather_data = get_weather_data(city)
        
        if weather_data:
            weather_message = format_weather_message(weather_data, city)
            send_telegram_message(chat_id, weather_message)
        else:
            if OPENWEATHER_API_KEY:
                send_telegram_message(chat_id, f"❌ No pude obtener el clima de *{city}*\n\nVerifica el nombre de la ciudad.")
            else:
                send_telegram_message(chat_id, "❌ API del clima no configurada.\n\nContacta al administrador para configurar OPENWEATHER_API_KEY.")
    
    elif text.startswith('/ubicacion'):
        parts = text.split(' ', 1)
        if len(parts) < 2:
            if user_id in user_locations:
                current_location = user_locations[user_id]
                send_telegram_message(chat_id, f"📍 Tu ubicación actual: *{current_location}*\n\nPara cambiar: `/ubicacion Nueva_Ciudad`")
            else:
                send_telegram_message(chat_id, "❌ Uso: `/ubicacion <ciudad>`\n\nEjemplo: `/ubicacion La Habana`")
            return
        
        city = parts[1]
        # Verificar que la ciudad existe consultando el clima
        weather_data = get_weather_data(city)
        
        if weather_data:
            user_locations[user_id] = city
            save_data()
            send_telegram_message(chat_id, f"✅ Ubicación guardada: *{city}*\n\nAhora puedes usar `/clima` sin especificar ciudad.")
        else:
            send_telegram_message(chat_id, f"❌ No encontré la ciudad *{city}*\n\nVerifica el nombre e intenta de nuevo.")
    
    elif text.startswith('/programar'):
        parts = text.split(' ', 2)
        if len(parts) < 3:
            keyboard = create_time_examples_keyboard()
            send_telegram_message(chat_id, 
                "❌ *Uso:* `/programar <tiempo> <mensaje>`\n\n"
                "*Ejemplos de formato:*", 
                reply_markup=keyboard)
            return
        
        time_str = parts[1]
        message_text = parts[2]
        
        scheduled_time = parse_time_advanced(time_str)
        if not scheduled_time:
            send_telegram_message(chat_id, 
                "❌ *Formato de tiempo inválido*\n\n"
                "*Formatos válidos:*\n"
                "• `5m` = 5 minutos\n"
                "• `2h` = 2 horas\n"
                "• `1d` = 1 día\n"
                "• `14:30` = Hoy 2:30 PM\n"
                "• `09:00` = Mañana 9:00 AM")
            return
        
        # Verificar que no sea en el pasado (excepto segundos para testing)
        if scheduled_time <= datetime.now() and not time_str.endswith('s'):
            send_telegram_message(chat_id, "❌ No puedes programar mensajes en el pasado")
            return
        
        message_id = str(int(datetime.now().timestamp() * 1000))
        scheduled_message = {
            'id': message_id,
            'chat_id': chat_id,
            'user_id': user_id,
            'message': message_text,
            'scheduled_time': scheduled_time.isoformat(),
            'created': datetime.now().isoformat(),
            'time_format': time_str
        }
        
        scheduled_messages.append(scheduled_message)
        save_data()
        
        # Calcular tiempo restante para mostrar
        time_diff = scheduled_time - datetime.now()
        if time_diff.days > 0:
            time_remaining = f"{time_diff.days} día(s)"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_remaining = f"{hours} hora(s)"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_remaining = f"{minutes} minuto(s)"
        else:
            time_remaining = f"{time_diff.seconds} segundo(s)"
        
        response = f"""✅ *Mensaje programado correctamente*

📝 *Mensaje:* {message_text}
⏰ *Envío:* {scheduled_time.strftime('%d/%m/%Y %H:%M')}
⏳ *Tiempo restante:* {time_remaining}
🆔 *ID:* `{message_id}`

_Usa /mensajes para ver todos tus mensajes programados_"""
        
        send_telegram_message(chat_id, response)
    
    elif text == '/mensajes':
        user_messages = [msg for msg in scheduled_messages if msg['chat_id'] == chat_id]
        
        if not user_messages:
            send_telegram_message(chat_id, "📭 No tienes mensajes programados\n\nUsa `/programar <tiempo> <mensaje>` para crear uno")
            return
        
        response = "📋 *Tus mensajes programados:*\n\n"
        
        for i, msg in enumerate(user_messages, 1):
            scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
            time_diff = scheduled_time - datetime.now()
            
            if time_diff.total_seconds() > 0:
                status = "⏳ Pendiente"
                if time_diff.days > 0:
                    remaining = f"{time_diff.days}d"
                elif time_diff.seconds > 3600:
                    remaining = f"{time_diff.seconds//3600}h"
                else:
                    remaining = f"{time_diff.seconds//60}m"
            else:
                status = "⏰ Listo para enviar"
                remaining = "Ahora"
            
            response += f"*{i}.* {msg['message']}\n"
            response += f"⏰ {scheduled_time.strftime('%d/%m %H:%M')} ({remaining})\n"
            response += f"📊 {status}\n"
            response += f"🆔 `{msg['id']}`\n\n"
        
        response += "_Usa /cancelar <ID> para cancelar un mensaje_"
        send_telegram_message(chat_id, response)
    
    elif text.startswith('/cancelar'):
        parts = text.split(' ', 1)
        if len(parts) < 2:
            send_telegram_message(chat_id, "❌ Uso: `/cancelar <ID>`\n\nUsa /mensajes para ver los IDs disponibles")
            return
        
        message_id = parts[1]
        original_count = len(scheduled_messages)
        scheduled_messages[:] = [msg for msg in scheduled_messages 
                               if msg['id'] != message_id or msg['chat_id'] != chat_id]
        
        if len(scheduled_messages) < original_count:
            save_data()
            send_telegram_message(chat_id, f"✅ *Mensaje cancelado*\n\n🆔 ID: `{message_id}`")
        else:
            send_telegram_message(chat_id, f"❌ *Mensaje no encontrado*\n\n🆔 ID: `{message_id}`\n\n_Usa /mensajes para ver IDs válidos_")
    
    elif text == '/estado':
        uptime = datetime.now() - bot_stats['uptime_start']
        user_count = len([msg for msg in scheduled_messages if msg['chat_id'] == chat_id])
        user_location = user_locations.get(user_id, "No configurada")
        
        response = f"""📊 *Estado del Bot v3.0*

✅ *Estado:* Activo y funcionando
⏰ *Tiempo activo:* {str(uptime).split('.')[0]}
🔄 *Reinicios:* {bot_stats['restarts_count']}

📈 *Estadísticas generales:*
• Comandos procesados: {bot_stats['commands_received']}
• Mensajes enviados: {bot_stats['messages_sent']}
• Consultas del clima: {bot_stats['weather_requests']}

👤 *Tu información:*
• Mensajes programados: {user_count}
• Ubicación guardada: {user_location}

🌐 *Sistema:*
• Total mensajes: {len(scheduled_messages)}
• Usuarios con ubicación: {len(user_locations)}

🕐 *Última actualización:* {datetime.now().strftime('%H:%M:%S')}

_Bot con clima y programación avanzada_ 🌟"""
        
        send_telegram_message(chat_id, response)
    
    else:
        # Mensaje no reconocido
        if not text.startswith('/'):
            send_telegram_message(chat_id, 
                f"👋 Recibí: \"{text}\"\n\n"
                "Usa /ayuda para ver todos los comandos disponibles\n"
                "O prueba /clima o /programar")

def check_scheduled():
    global scheduled_messages, bot_stats
    
    try:
        current_time = datetime.now()
        to_remove = []
        
        for i, msg in enumerate(scheduled_messages):
            try:
                scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
                if current_time >= scheduled_time:
                    message_text = f"⏰ *Recordatorio programado:*\n\n{msg['message']}"
                    
                    if send_telegram_message(msg['chat_id'], message_text):
                        logger.info(f"Recordatorio enviado: {msg['message']}")
                        bot_stats['messages_sent'] += 1
                    to_remove.append(i)
            except Exception as e:
                logger.error(f"Error procesando mensaje: {e}")
                to_remove.append(i)
        
        for i in reversed(to_remove):
            scheduled_messages.pop(i)
        
        if to_remove:
            save_data()
            
    except Exception as e:
        logger.error(f"Error en scheduler: {e}")

def run_scheduler():
    while True:
        try:
            check_scheduled()
            time.sleep(30)
        except Exception as e:
            logger.error(f"Error en scheduler: {e}")
            time.sleep(60)

def run_bot():
    offset = 0
    
    while True:
        try:
            updates = get_telegram_updates(offset)
            
            if updates.get('ok'):
                for update in updates.get('result', []):
                    offset = update['update_id'] + 1
                    
                    if 'message' in update:
                        message = update['message']
                        if 'text' in message:
                            handle_command(message)
            else:
                logger.error("Error obteniendo updates")
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Error en bot: {e}")
            bot_stats['restarts_count'] += 1
            time.sleep(10)

# Flask para keepalive
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'Smart Messenger Bot v3.0 - Enhanced',
        'features': ['advanced_scheduling', 'weather_api', 'user_locations'],
        'uptime': str(datetime.now() - bot_stats['uptime_start']).split('.')[0],
        'stats': bot_stats,
        'data': {
            'scheduled_messages': len(scheduled_messages),
            'user_locations': len(user_locations)
        },
        'last_check': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'OK', 
        'version': '3.0',
        'weather_api': OPENWEATHER_API_KEY is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/stats')
def stats():
    return jsonify({
        'bot_stats': bot_stats,
        'scheduled_count': len(scheduled_messages),
        'locations_count': len(user_locations),
        'features': {
            'weather': OPENWEATHER_API_KEY is not None,
            'advanced_scheduling': True,
            'user_locations': True
        }
    })

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN requerido")
        return
    
    logger.info("🌟 Iniciando Smart Messenger Bot v3.0...")
    logger.info(f"🌤️ API Clima: {'✅ Configurada' if OPENWEATHER_API_KEY else '❌ No configurada'}")
    
    load_data()
    
    # Iniciar scheduler
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Iniciar Flask
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Iniciar bot
    run_bot()

if __name__ == '__main__':
    main()
