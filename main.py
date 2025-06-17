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
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

scheduled_messages = []
bot_stats = {
    'messages_sent': 0,
    'commands_received': 0,
    'uptime_start': datetime.now(),
    'restarts_count': 0
}

def load_messages():
    global scheduled_messages
    try:
        if os.path.exists('messages.json'):
            with open('messages.json', 'r') as f:
                scheduled_messages = json.load(f)
                logger.info(f"Cargados {len(scheduled_messages)} mensajes")
    except Exception as e:
        logger.error(f"Error cargando: {e}")
        scheduled_messages = []

def save_messages():
    try:
        with open('messages.json', 'w') as f:
            json.dump(scheduled_messages, f)
    except Exception as e:
        logger.error(f"Error guardando: {e}")

def send_telegram_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
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

def parse_time(time_str):
    try:
        if time_str.endswith('m'):
            minutes = int(time_str[:-1])
            return datetime.now() + timedelta(minutes=minutes)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            return datetime.now() + timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[:-1])
            return datetime.now() + timedelta(days=days)
    except:
        pass
    return None

def handle_command(message):
    global bot_stats, scheduled_messages
    
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_name = message['from'].get('first_name', 'Usuario')
    
    bot_stats['commands_received'] += 1
    
    if text == '/start':
        welcome = f"""¡Hola {user_name}! 👋

🤖 *Smart Messenger Bot v2.0*

📋 *Comandos:*
/programar <tiempo> <mensaje> - Programar mensaje
/mensajes - Ver mensajes programados
/cancelar <ID> - Cancelar mensaje
/estado - Estado del bot
/ayuda - Ver ayuda

*Ejemplo:* `/programar 5m Recordatorio`"""
        
        send_telegram_message(chat_id, welcome)
    
    elif text == '/ayuda':
        help_text = """🤖 *Ayuda - Smart Messenger Bot*

📋 *Comandos:*

🔸 `/programar <tiempo> <mensaje>`
   *Ejemplos:*
   • `/programar 5m Tomar medicina`
   • `/programar 2h Llamada importante`
   • `/programar 1d Evento mañana`

🔸 `/mensajes` - Ver programados
🔸 `/cancelar <ID>` - Cancelar mensaje
🔸 `/estado` - Estado del bot

⏰ *Formatos:*
• `5m` = 5 minutos
• `2h` = 2 horas
• `1d` = 1 día"""
        
        send_telegram_message(chat_id, help_text)
    
    elif text.startswith('/programar'):
        parts = text.split(' ', 2)
        if len(parts) < 3:
            send_telegram_message(chat_id, "❌ Uso: `/programar <tiempo> <mensaje>`\n\nEjemplo: `/programar 5m Recordatorio`")
            return
        
        time_str = parts[1]
        message_text = parts[2]
        
        scheduled_time = parse_time(time_str)
        if not scheduled_time:
            send_telegram_message(chat_id, "❌ Formato inválido. Usa: `5m`, `2h`, `1d`")
            return
        
        message_id = str(int(datetime.now().timestamp() * 1000))
        scheduled_message = {
            'id': message_id,
            'chat_id': chat_id,
            'message': message_text,
            'scheduled_time': scheduled_time.isoformat(),
            'created': datetime.now().isoformat()
        }
        
        scheduled_messages.append(scheduled_message)
        save_messages()
        
        response = f"""✅ *Mensaje programado*

📝 *Mensaje:* {message_text}
⏰ *Envío:* {scheduled_time.strftime('%d/%m %H:%M')}
🆔 *ID:* `{message_id}`"""
        
        send_telegram_message(chat_id, response)
    
    elif text == '/mensajes':
        user_messages = [msg for msg in scheduled_messages if msg['chat_id'] == chat_id]
        
        if not user_messages:
            send_telegram_message(chat_id, "📭 No tienes mensajes programados")
            return
        
        response = "📋 *Tus mensajes:*\n\n"
        for i, msg in enumerate(user_messages, 1):
            scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
            response += f"*{i}.* {msg['message']}\n"
            response += f"⏰ {scheduled_time.strftime('%d/%m %H:%M')}\n"
            response += f"🆔 `{msg['id']}`\n\n"
        
        send_telegram_message(chat_id, response)
    
    elif text.startswith('/cancelar'):
        parts = text.split(' ', 1)
        if len(parts) < 2:
            send_telegram_message(chat_id, "❌ Uso: `/cancelar <ID>`\n\nUsa /mensajes para ver IDs")
            return
        
        message_id = parts[1]
        original_count = len(scheduled_messages)
        scheduled_messages[:] = [msg for msg in scheduled_messages 
                               if msg['id'] != message_id or msg['chat_id'] != chat_id]
        
        if len(scheduled_messages) < original_count:
            save_messages()
            send_telegram_message(chat_id, f"✅ Mensaje cancelado\n🆔 ID: `{message_id}`")
        else:
            send_telegram_message(chat_id, f"❌ Mensaje no encontrado\n🆔 ID: `{message_id}`")
    
    elif text == '/estado':
        uptime = datetime.now() - bot_stats['uptime_start']
        user_count = len([msg for msg in scheduled_messages if msg['chat_id'] == chat_id])
        
        response = f"""📊 *Estado del Bot*

✅ *Estado:* Activo
⏰ *Tiempo activo:* {str(uptime).split('.')[0]}
🔄 *Reinicios:* {bot_stats['restarts_count']}

📈 *Estadísticas:*
• Comandos: {bot_stats['commands_received']}
• Enviados: {bot_stats['messages_sent']}
• Tus mensajes: {user_count}
• Total sistema: {len(scheduled_messages)}"""
        
        send_telegram_message(chat_id, response)

def check_scheduled():
    global scheduled_messages, bot_stats
    
    try:
        current_time = datetime.now()
        to_remove = []
        
        for i, msg in enumerate(scheduled_messages):
            try:
                scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
                if current_time >= scheduled_time:
                    if send_telegram_message(msg['chat_id'], msg['message']):
                        logger.info(f"Mensaje enviado: {msg['message']}")
                        bot_stats['messages_sent'] += 1
                    to_remove.append(i)
            except Exception as e:
                logger.error(f"Error procesando mensaje: {e}")
                to_remove.append(i)
        
        for i in reversed(to_remove):
            scheduled_messages.pop(i)
        
        if to_remove:
            save_messages()
            
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
        'status': 'Smart Messenger Bot Activo',
        'uptime': str(datetime.now() - bot_stats['uptime_start']).split('.')[0],
        'messages_sent': bot_stats['messages_sent'],
        'commands_received': bot_stats['commands_received'],
        'scheduled_messages': len(scheduled_messages),
        'last_check': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'OK', 'timestamp': datetime.now().isoformat()})

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN requerido")
        return
    
    logger.info("🤖 Iniciando Smart Messenger Bot...")
    
    load_messages()
    
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
