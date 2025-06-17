#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from threading import Thread
from flask import Flask, jsonify
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token del bot de Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN no encontrado en variables de entorno")
    exit(1)

# Archivo para persistir mensajes programados
MESSAGES_FILE = 'mensajes_programados.json'

# Variables globales
updater = None
scheduled_messages = []
bot_stats = {
    'messages_sent': 0,
    'commands_received': 0,
    'uptime_start': datetime.now(),
    'last_restart': None,
    'restarts_count': 0
}

def load_scheduled_messages():
    """Cargar mensajes programados desde archivo"""
    global scheduled_messages
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                scheduled_messages = data.get('messages', [])
                logger.info(f"Cargados {len(scheduled_messages)} mensajes programados")
        else:
            scheduled_messages = []
            save_scheduled_messages()
    except Exception as e:
        logger.error(f"Error cargando mensajes: {e}")
        scheduled_messages = []

def save_scheduled_messages():
    """Guardar mensajes programados en archivo"""
    try:
        data = {
            'messages': scheduled_messages,
            'last_updated': datetime.now().isoformat()
        }
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error guardando mensajes: {e}")

def check_scheduled_messages():
    """Verificar y enviar mensajes programados"""
    global scheduled_messages, bot_stats
    
    try:
        current_time = datetime.now()
        messages_to_remove = []
        
        for i, msg in enumerate(scheduled_messages):
            try:
                scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
                if current_time >= scheduled_time:
                    # Enviar mensaje
                    bot = Bot(token=TELEGRAM_BOT_TOKEN)
                    bot.send_message(
                        chat_id=msg['chat_id'],
                        text=msg['message']
                    )
                    
                    logger.info(f"Mensaje enviado a {msg['chat_id']}: {msg['message']}")
                    bot_stats['messages_sent'] += 1
                    messages_to_remove.append(i)
                    
            except Exception as e:
                logger.error(f"Error enviando mensaje programado: {e}")
                messages_to_remove.append(i)
        
        # Remover mensajes enviados
        for i in reversed(messages_to_remove):
            scheduled_messages.pop(i)
        
        if messages_to_remove:
            save_scheduled_messages()
            
    except Exception as e:
        logger.error(f"Error en check_scheduled_messages: {e}")

def start_command(update: Update, context: CallbackContext):
    """Comando /start"""
    global bot_stats
    bot_stats['commands_received'] += 1
    
    welcome_text = f"""¡Hola {update.effective_user.first_name}! 👋

🤖 *Smart Messenger Bot v2.0*
_Bot robusto con reconexión automática_

🚀 *Funcionalidades:*
• Programa mensajes automáticos
• Persistencia garantizada 
• Reconexión automática
• Monitoreo 24/7

📋 *Comandos disponibles:*
/programar - Programar mensaje
/mensajes - Ver mensajes programados
/cancelar - Cancelar mensaje
/estado - Estado del bot
/ayuda - Ver ayuda completa

¡Empezemos! Usa /ayuda para más información."""
    
    update.message.reply_text(welcome_text, parse_mode='Markdown')

def help_command(update: Update, context: CallbackContext):
    """Comando /ayuda"""
    global bot_stats
    bot_stats['commands_received'] += 1
    
    help_text = """🤖 *Smart Messenger Bot - Ayuda*

📋 *Comandos disponibles:*

🔸 `/programar <tiempo> <mensaje>`
   Programa un mensaje para enviar después
   
   *Ejemplos:*
   • `/programar 5m Recordatorio en 5 minutos`
   • `/programar 2h Reunión en 2 horas`
   • `/programar 1d Evento mañana`

🔸 `/mensajes` - Ver todos tus mensajes programados

🔸 `/cancelar <ID>` - Cancelar mensaje por ID

🔸 `/estado` - Ver estadísticas del bot

🔸 `/ayuda` - Ver esta ayuda

⏰ *Formatos de tiempo:*
• `5m` = 5 minutos
• `2h` = 2 horas  
• `1d` = 1 día
• `3w` = 3 semanas

💡 *Ejemplos prácticos:*
```
/programar 30m Tomar medicamento
/programar 2h Llamar al doctor
/programar 1d Reunión importante mañana
```

¿Necesitas más ayuda? ¡Pregúntame!"""
    
    update.message.reply_text(help_text, parse_mode='Markdown')

def parse_time_string(time_str: str) -> Optional[datetime]:
    """Convertir string de tiempo a datetime"""
    try:
        # Extraer número y unidad
        if time_str[-1] == 'm':  # minutos
            minutes = int(time_str[:-1])
            return datetime.now() + timedelta(minutes=minutes)
        elif time_str[-1] == 'h':  # horas
            hours = int(time_str[:-1])
            return datetime.now() + timedelta(hours=hours)
        elif time_str[-1] == 'd':  # días
            days = int(time_str[:-1])
            return datetime.now() + timedelta(days=days)
        elif time_str[-1] == 'w':  # semanas
            weeks = int(time_str[:-1])
            return datetime.now() + timedelta(weeks=weeks)
    except:
        pass
    return None

def programar_command(update: Update, context: CallbackContext):
    """Comando /programar"""
    global bot_stats, scheduled_messages
    bot_stats['commands_received'] += 1
    
    try:
        if len(context.args) < 2:
            update.message.reply_text(
                "❌ *Uso incorrecto*\n\n"
                "*Formato:* `/programar <tiempo> <mensaje>`\n\n"
                "*Ejemplos:*\n"
                "• `/programar 5m Recordatorio en 5 minutos`\n"
                "• `/programar 2h Reunión en 2 horas`\n"
                "• `/programar 1d Evento mañana`",
                parse_mode='Markdown'
            )
            return
        
        time_str = context.args[0]
        message = ' '.join(context.args[1:])
        
        # Parsear tiempo
        scheduled_time = parse_time_string(time_str)
        if not scheduled_time:
            update.message.reply_text(
                "❌ *Formato de tiempo inválido*\n\n"
                "*Formatos válidos:*\n"
                "• `5m` = 5 minutos\n"
                "• `2h` = 2 horas\n"
                "• `1d` = 1 día\n"
                "• `3w` = 3 semanas",
                parse_mode='Markdown'
            )
            return
        
        # Crear mensaje programado
        message_id = str(int(datetime.now().timestamp() * 1000))
        scheduled_message = {
            'id': message_id,
            'chat_id': update.effective_chat.id,
            'user_id': update.effective_user.id,
            'message': message,
            'scheduled_time': scheduled_time.isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        scheduled_messages.append(scheduled_message)
        save_scheduled_messages()
        
        update.message.reply_text(
            f"✅ *Mensaje programado correctamente*\n\n"
            f"📝 *Mensaje:* {message}\n"
            f"⏰ *Envío:* {scheduled_time.strftime('%d/%m/%Y %H:%M')}\n"
            f"🆔 *ID:* `{message_id}`\n\n"
            f"_Usa /mensajes para ver todos tus mensajes programados_",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error en comando programar: {e}")
        update.message.reply_text("❌ Error al programar mensaje. Intenta de nuevo.")

def mensajes_command(update: Update, context: CallbackContext):
    """Comando /mensajes"""
    global bot_stats, scheduled_messages
    bot_stats['commands_received'] += 1
    
    try:
        user_messages = [msg for msg in scheduled_messages 
                        if msg['chat_id'] == update.effective_chat.id]
        
        if not user_messages:
            update.message.reply_text("📭 No tienes mensajes programados.")
            return
        
        response = "📋 *Tus mensajes programados:*\n\n"
        
        for i, msg in enumerate(user_messages, 1):
            scheduled_time = datetime.fromisoformat(msg['scheduled_time'])
            response += f"*{i}.* 📝 {msg['message']}\n"
            response += f"⏰ {scheduled_time.strftime('%d/%m/%Y %H:%M')}\n"
            response += f"🆔 `{msg['id']}`\n\n"
        
        response += "_Usa /cancelar <ID> para cancelar un mensaje_"
        
        update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando mensajes: {e}")
        update.message.reply_text("❌ Error al obtener mensajes.")

def cancelar_command(update: Update, context: CallbackContext):
    """Comando /cancelar"""
    global bot_stats, scheduled_messages
    bot_stats['commands_received'] += 1
    
    try:
        if not context.args:
            update.message.reply_text(
                "❌ *Uso:* `/cancelar <ID>`\n\n"
                "_Usa /mensajes para ver los IDs disponibles_",
                parse_mode='Markdown'
            )
            return
        
        message_id = context.args[0]
        
        # Buscar y eliminar mensaje
        original_count = len(scheduled_messages)
        scheduled_messages[:] = [msg for msg in scheduled_messages 
                               if msg['id'] != message_id or msg['chat_id'] != update.effective_chat.id]
        
        if len(scheduled_messages) < original_count:
            save_scheduled_messages()
            update.message.reply_text(
                f"✅ *Mensaje cancelado*\n\n"
                f"🆔 ID: `{message_id}`",
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text(
                f"❌ *Mensaje no encontrado*\n\n"
                f"🆔 ID: `{message_id}`\n\n"
                f"_Usa /mensajes para ver IDs válidos_",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error en comando cancelar: {e}")
        update.message.reply_text("❌ Error al cancelar mensaje.")

def estado_command(update: Update, context: CallbackContext):
    """Comando /estado"""
    global bot_stats, scheduled_messages
    bot_stats['commands_received'] += 1
    
    try:
        uptime = datetime.now() - bot_stats['uptime_start']
        user_messages = len([msg for msg in scheduled_messages 
                           if msg['chat_id'] == update.effective_chat.id])
        
        response = f"""📊 *Estado del Bot*

✅ *Estado:* Activo y funcionando
⏰ *Tiempo activo:* {str(uptime).split('.')[0]}
🔄 *Reinicios:* {bot_stats['restarts_count']}

📈 *Estadísticas:*
• Comandos procesados: {bot_stats['commands_received']}
• Mensajes enviados: {bot_stats['messages_sent']}
• Tus mensajes programados: {user_messages}
• Total mensajes sistema: {len(scheduled_messages)}

🕐 *Última verificación:* {datetime.now().strftime('%H:%M:%S')}

_Bot robusto con reconexión automática_ ✨"""
        
        update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando estado: {e}")
        update.message.reply_text("❌ Error al obtener estado.")

def handle_text(update: Update, context: CallbackContext):
    """Manejar mensajes de texto"""
    if not update.message.text.startswith('/'):
        update.message.reply_text(
            f"👋 Recibí: \"{update.message.text}\"\n\n"
            "Usa /ayuda para ver todos los comandos disponibles."
        )

def setup_bot():
    """Configurar y crear el updater del bot"""
    global updater
    
    try:
        # Crear updater
        updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Agregar handlers
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("ayuda", help_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("programar", programar_command))
        dispatcher.add_handler(CommandHandler("mensajes", mensajes_command))
        dispatcher.add_handler(CommandHandler("cancelar", cancelar_command))
        dispatcher.add_handler(CommandHandler("estado", estado_command))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        
        logger.info("Bot configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error configurando bot: {e}")
        return False

def run_scheduler():
    """Ejecutar scheduler en thread separado"""
    while True:
        try:
            check_scheduled_messages()
            time.sleep(30)  # Verificar cada 30 segundos
        except Exception as e:
            logger.error(f"Error en scheduler: {e}")
            time.sleep(60)

def run_bot_with_restart():
    """Ejecutar bot con reinicio automático"""
    global bot_stats, updater
    
    while True:
        try:
            logger.info("🤖 Iniciando Smart Messenger Bot...")
            
            if not setup_bot():
                logger.error("Error configurando bot")
                time.sleep(30)
                continue
            
            logger.info("✅ Bot iniciado correctamente")
            logger.info(f"📱 {len(scheduled_messages)} mensajes programados cargados")
            
            # Iniciar polling
            updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                read_latency=2.0,
                drop_pending_updates=True
            )
            
            # Mantener bot activo
            updater.idle()
            
        except Exception as e:
            logger.error(f"Error en bot: {e}")
            bot_stats['restarts_count'] += 1
            bot_stats['last_restart'] = datetime.now()
            
            try:
                if updater:
                    updater.stop()
            except:
                pass
            
            logger.info("🔄 Reiniciando bot en 10 segundos...")
            time.sleep(10)

# Flask app para keepalive
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'Smart Messenger Bot v2.0 - Activo',
        'uptime': str(datetime.now() - bot_stats['uptime_start']).split('.')[0],
        'messages_sent': bot_stats['messages_sent'],
        'commands_received': bot_stats['commands_received'],
        'scheduled_messages': len(scheduled_messages),
        'restarts': bot_stats['restarts_count'],
        'last_check': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'OK',
        'bot_active': updater is not None,
        'scheduled_count': len(scheduled_messages),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/stats')
def stats():
    return jsonify(bot_stats)

def run_flask():
    """Ejecutar Flask en thread separado"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    """Función principal"""
    # Cargar mensajes programados
    load_scheduled_messages()
    
    # Iniciar scheduler en thread separado
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Iniciar Flask en thread separado
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Ejecutar bot con reinicio automático
    run_bot_with_restart()

if __name__ == '__main__':
    main()
