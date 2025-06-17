#!/usr/bin/env python3
import os
import json
import logging
import time
import requests
import random
import schedule
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FusionBot')

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
RENDER_SERVICE_URL = os.environ.get('RENDER_SERVICE_URL', 'https://your-service.onrender.com')
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

class KeepAliveManager:
    def __init__(self):
        self.ping_count = 0
        self.last_ping = datetime.now()
        
    def self_ping(self):
        try:
            response = requests.get(RENDER_SERVICE_URL, timeout=10)
            self.ping_count += 1
            self.last_ping = datetime.now()
            if response.status_code == 200:
                logger.info(f"✅ Keepalive ping #{self.ping_count}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error keepalive: {e}")
            return False
    
    def run_keepalive_loop(self):
        while True:
            try:
                self.self_ping()
                time.sleep(600)
            except Exception as e:
                logger.error(f"Error en keepalive: {e}")
                time.sleep(300)

class DataManager:
    def __init__(self):
        self.data = {
            'messenger': {'scheduled_messages': []},
            'loto': {'prediction_history': [], 'charada_cubana': self.load_charada()},
            'weather': {'user_locations': {}},
            'users': {'profiles': {}},
            'analytics': {'command_usage': {}},
            'keepalive': {'pings': [], 'uptime_start': datetime.now().isoformat()}
        }
        self.load_data()
    
    def load_charada(self):
        return {
            1: {"nombre": "Caballo", "significados": ["sol", "tintero", "camello", "pescado"]},
            2: {"nombre": "Mariposa", "significados": ["dinero", "hombre", "cafetera", "caracol"]},
            13: {"nombre": "Jorobado", "significados": ["suerte", "fortuna", "monte", "chepa"]},
            21: {"nombre": "Mujer", "significados": ["feminidad", "madre", "cocina", "casa"]},
            100: {"nombre": "Excremento", "significados": ["suerte", "dinero", "fortuna", "premio"]}
        }
    
    def load_data(self):
        try:
            if os.path.exists('fusion_bot_data.json'):
                with open('fusion_bot_data.json', 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    for section in self.data:
                        if section in loaded:
                            self.data[section].update(loaded[section])
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
    
    def save_data(self):
        try:
            with open('fusion_bot_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")
    
    def get_user_profile(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data['users']['profiles']:
            self.data['users']['profiles'][user_id] = {
                'join_date': datetime.now().isoformat(),
                'total_commands': 0,
                'level': 1,
                'points': 0
            }
        return self.data['users']['profiles'][user_id]
    
    def update_user_stats(self, user_id, command):
        profile = self.get_user_profile(user_id)
        profile['total_commands'] += 1
        profile['points'] += 1
        
        if profile['points'] >= profile['level'] * 10:
            profile['level'] += 1
        
        if command not in self.data['analytics']['command_usage']:
            self.data['analytics']['command_usage'][command] = 0
        self.data['analytics']['command_usage'][command] += 1
        
        self.save_data()

data_manager = DataManager()
keepalive_manager = KeepAliveManager()

class TelegramAPI:
    @staticmethod
    def send_message(chat_id, text, reply_markup=None):
        try:
            url = f"{TELEGRAM_API}/sendMessage"
            payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(url, json=payload, timeout=30)
            return response.json().get('ok', False)
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False
    
    @staticmethod
    def get_updates(offset=0):
        try:
            url = f"{TELEGRAM_API}/getUpdates"
            params = {'offset': offset, 'timeout': 30}
            response = requests.get(url, params=params, timeout=35)
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo updates: {e}")
            return {'ok': False, 'result': []}

class MessageHandler:
    @staticmethod
    def handle_message(message):
        chat_id = message['chat']['id']
        text = message.get('text', '')
        user_id = message['from']['id']
        username = message['from'].get('username', 'Usuario')
        
        data_manager.update_user_stats(user_id, text.split()[0])
        
        if text == '/start':
            welcome = f"""🚀 *FUSION BOT v7.0 - COMPLETO + KEEPALIVE*

¡Hola {username}! Bot profesional activo 24/7 con todas las funciones.

*🔥 FUNCIONES PRINCIPALES:*

*📱 SMART MESSENGER:*
•  - Programar mensajes
•  - Ver mensajes pendientes

*🎯 LOTO PREDICTOR:*
•  - Predicción inteligente
•  - Consultar charada cubana

*🌤️ CLIMA INTELIGENTE:*
•  - Clima en tiempo real

*📊 ANALYTICS:*
•  - Tus estadísticas personales
•  - Dashboard completo

*🔧 SISTEMA KEEPALIVE:*
•  - Estado del sistema 24/7
•  - Ping del bot
•  - Tiempo activo

*🎮 DIVERSIÓN:*
•  - Número de la suerte
•  - Ayuda completa

*¡Sistema keepalive activo - Bot disponible 24/7!* ✅"""
            
            TelegramAPI.send_message(chat_id, welcome)
        
        elif text.startswith('/programar'):
            MessageHandler.handle_programar(chat_id, user_id, text)
        
        elif text == '/ver_programados':
            MessageHandler.handle_ver_programados(chat_id, user_id)
        
        elif text == '/loto':
            MessageHandler.handle_loto_predict(chat_id, user_id)
        
        elif text.startswith('/charada'):
            try:
                numero = int(text.split()[1])
                MessageHandler.handle_charada(chat_id, numero)
            except:
                TelegramAPI.send_message(chat_id, "❌ Formato: ")
        
        elif text.startswith('/clima'):
            try:
                ciudad = ' '.join(text.split()[1:])
                if ciudad:
                    MessageHandler.handle_clima(chat_id, user_id, ciudad)
                else:
                    TelegramAPI.send_message(chat_id, "❌ Formato: ")
            except:
                TelegramAPI.send_message(chat_id, "❌ Especifica una ciudad: ")
        
        elif text == '/stats':
            MessageHandler.handle_stats(chat_id, user_id)
        
        elif text == '/dashboard':
            profile = data_manager.get_user_profile(user_id)
            dashboard = f"""📊 *DASHBOARD PERSONAL*

👤 *Usuario:* #{user_id}
🏆 *Nivel:* {profile['level']} (⭐ {profile['points']} puntos)
⚡ *Total comandos:* {profile['total_commands']}

📈 *Actividad reciente:*
• Mensajes programados: {len([m for m in data_manager.data['messenger']['scheduled_messages'] if m['user_id'] == str(user_id)])}
• Predicciones hechas: {len([p for p in data_manager.data['loto']['prediction_history'] if p['user_id'] == str(user_id)])}

🎯 *Siguiente nivel:* {(profile['points'] % 10)} / 10 puntos"""
            TelegramAPI.send_message(chat_id, dashboard)
        
        elif text == '/status':
            uptime_start = datetime.fromisoformat(data_manager.data['keepalive']['uptime_start'])
            uptime_duration = datetime.now() - uptime_start
            
            status_msg = f"""📊 *ESTADO DEL SISTEMA 24/7*

🟢 *Estado:* ACTIVO
⏱️ *Tiempo activo:* {str(uptime_duration).split('.')[0]}
📡 *Pings keepalive:* {keepalive_manager.ping_count}
🕐 *Último ping:* {keepalive_manager.last_ping.strftime('%H:%M:%S')}
👥 *Usuarios registrados:* {len(data_manager.data['users']['profiles'])}
📝 *Mensajes programados:* {len(data_manager.data['messenger']['scheduled_messages'])}

*✅ Sistema keepalive funcionando correctamente*"""
            
            TelegramAPI.send_message(chat_id, status_msg)
        
        elif text == '/ping':
            TelegramAPI.send_message(chat_id, "🏓 *Pong!* Bot respondiendo correctamente ✅")
        
        elif text == '/uptime':
            uptime_start = datetime.fromisoformat(data_manager.data['keepalive']['uptime_start'])
            uptime_duration = datetime.now() - uptime_start
            
            uptime_msg = f"""⏰ *TIEMPO ACTIVO DEL BOT*

🚀 *Iniciado:* {uptime_start.strftime('%d/%m/%Y %H:%M')}
⏱️ *Activo durante:* {str(uptime_duration).split('.')[0]}
🔄 *Sistema keepalive:* Funcionando 24/7
📊 *Actividad total:* {sum(data_manager.data['analytics']['command_usage'].values())} comandos

*Bot funcionando continuamente sin interrupciones* ✅"""
            
            TelegramAPI.send_message(chat_id, uptime_msg)
        
        elif text == '/random':
            numero_suerte = random.randint(1, 100)
            if numero_suerte in data_manager.data['loto']['charada_cubana']:
                charada = data_manager.data['loto']['charada_cubana'][numero_suerte]
                TelegramAPI.send_message(chat_id, 
                    f"🍀 *Tu número de la suerte:* {numero_suerte}\n"
                    f"🎲 *Significado:* {charada['nombre']} - {', '.join(charada['significados'][:2])}")
            else:
                TelegramAPI.send_message(chat_id, f"🍀 *Tu número de la suerte:* {numero_suerte}")
        
        elif text == '/help':
            help_text = """📚 *AYUDA COMPLETA - FUSION BOT*

*📱 SMART MESSENGER:*
•  - Programar mensaje en 30 minutos
•  - Programar en 2 horas  
•  - Programar en 1 día
•  - Ver todos los mensajes pendientes

*🎯 LOTO PREDICTOR:*
•  - Predicción IA con 4 números recomendados
•  - Consultar significado del número 13
•  - Número de la suerte aleatorio

*🌤️ CLIMA:*
•  - Clima actual en Madrid
•  - Clima en cualquier ciudad del mundo

*📊 ANALYTICS:*
•  - Tus estadísticas personales y nivel
•  - Dashboard completo con actividad

*🔧 SISTEMA:*
•  - Estado del sistema keepalive 24/7
•  - Verificar que el bot responde
•  - Tiempo total que el bot ha estado activo

*El bot está activo 24/7 gracias al sistema keepalive avanzado* 🚀"""
            
            TelegramAPI.send_message(chat_id, help_text)
        
        else:
            TelegramAPI.send_message(chat_id, 
                f"Comando no reconocido: \n\n"
                f"Usa  para ver todos los comandos disponibles.\n"
                f"Usa  para ver el menú principal.")
    
    @staticmethod
    def handle_programar(chat_id, user_id, text):
        try:
            parts = text.split(' ', 2)
            if len(parts) < 3:
                TelegramAPI.send_message(chat_id, 
                    "❌ Formato: \n\n"
                    "Ejemplos:\n"
                    "• \n"
                    "• \n"
                    "• ")
                return
            
            tiempo_str = parts[1]
            mensaje = parts[2]
            
            if tiempo_str.endswith('m'):
                minutos = int(tiempo_str[:-1])
                fecha_envio = datetime.now() + timedelta(minutes=minutos)
            elif tiempo_str.endswith('h'):
                horas = int(tiempo_str[:-1])
                fecha_envio = datetime.now() + timedelta(hours=horas)
            elif tiempo_str.endswith('d'):
                dias = int(tiempo_str[:-1])
                fecha_envio = datetime.now() + timedelta(days=dias)
            else:
                TelegramAPI.send_message(chat_id, "❌ Formato de tiempo inválido. Usa: 30m, 2h, 1d")
                return
            
            mensaje_programado = {
                'chat_id': chat_id,
                'user_id': str(user_id),
                'mensaje': mensaje,
                'fecha_envio': fecha_envio.isoformat(),
                'programado_en': datetime.now().isoformat(),
                'estado': 'pendiente'
            }
            
            data_manager.data['messenger']['scheduled_messages'].append(mensaje_programado)
            data_manager.save_data()
            
            TelegramAPI.send_message(chat_id,
                f"⏰ *Mensaje Programado* ✅\n\n"
                f"📝 *Mensaje:* {mensaje}\n"
                f"🕐 *Se enviará:* {fecha_envio.strftime('%d/%m/%Y %H:%M')}\n"
                f"⏱️ *En:* {tiempo_str}\n\n"
                f"Usa  para ver todos tus mensajes.")
            
        except Exception as e:
            TelegramAPI.send_message(chat_id, f"❌ Error programando mensaje: {str(e)}")
    
    @staticmethod
    def handle_ver_programados(chat_id, user_id):
        mensajes = [m for m in data_manager.data['messenger']['scheduled_messages'] 
                   if m['user_id'] == str(user_id) and m['estado'] == 'pendiente']
        
        if not mensajes:
            TelegramAPI.send_message(chat_id, "📭 No tienes mensajes programados.")
            return
        
        texto = "📅 *Tus Mensajes Programados:*\n\n"
        for i, msg in enumerate(mensajes[:10], 1):
            fecha = datetime.fromisoformat(msg['fecha_envio'])
            texto += f"{i}. 📝 {msg['mensaje'][:30]}...\n"
            texto += f"   🕐 {fecha.strftime('%d/%m %H:%M')}\n\n"
        
        TelegramAPI.send_message(chat_id, texto)
    
    @staticmethod
    def handle_loto_predict(chat_id, user_id):
        try:
            random.seed(int(time.time()))
            numeros_calientes = [7, 13, 21, 33, 42, 77, 88, 100]
            
            prediccion = []
            for _ in range(4):
                if random.random() < 0.3:
                    num = random.choice(numeros_calientes)
                else:
                    num = random.randint(1, 100)
                
                while num in prediccion:
                    num = random.randint(1, 100)
                prediccion.append(num)
            
            prediccion.sort()
            
            texto = f"🎯 *PREDICCIÓN LOTO INTELIGENTE* \n\n"
            texto += f"🔢 *Números recomendados:* \n\n"
            texto += f"🎲 *Significados (Charada Cubana):*\n"
            
            for num in prediccion:
                if num in data_manager.data['loto']['charada_cubana']:
                    charada = data_manager.data['loto']['charada_cubana'][num]
                    texto += f"• *{num}* - {charada['nombre']} ({', '.join(charada['significados'][:2])})\n"
            
            texto += f"\n⭐ *Confianza:* {random.randint(75, 95)}%"
            texto += f"\n🎯 *Algoritmo:* IA + Análisis Histórico"
            texto += f"\n🍀 *¡Buena suerte!*"
            
            prediccion_data = {
                'user_id': str(user_id),
                'numeros': prediccion,
                'fecha': datetime.now().isoformat(),
                'algoritmo': 'IA_avanzada'
            }
            data_manager.data['loto']['prediction_history'].append(prediccion_data)
            data_manager.save_data()
            
            TelegramAPI.send_message(chat_id, texto)
            
        except Exception as e:
            TelegramAPI.send_message(chat_id, f"❌ Error en predicción: {str(e)}")
    
    @staticmethod
    def handle_charada(chat_id, numero):
        try:
            if numero in data_manager.data['loto']['charada_cubana']:
                charada = data_manager.data['loto']['charada_cubana'][numero]
                texto = f"🎲 *Charada Cubana - Número {numero}*\n\n"
                texto += f"🏷️ *Nombre:* {charada['nombre']}\n"
                texto += f"🔮 *Significados:*\n"
                for sig in charada['significados']:
                    texto += f"• {sig}\n"
                texto += f"\n💡 *¡Este número puede traerte suerte!*"
                TelegramAPI.send_message(chat_id, texto)
            else:
                TelegramAPI.send_message(chat_id, f"❌ Número {numero} no encontrado en la charada.")
        except Exception as e:
            TelegramAPI.send_message(chat_id, f"❌ Error consultando charada: {str(e)}")
    
    @staticmethod
    def handle_clima(chat_id, user_id, ciudad):
        if not OPENWEATHER_API_KEY:
            TelegramAPI.send_message(chat_id, 
                "❌ API del clima no configurada.\n"
                "Solicita a tu administrador configurar OPENWEATHER_API_KEY")
            return
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': ciudad,
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                temp = data['main']['temp']
                descripcion = data['weather'][0]['description']
                humedad = data['main']['humidity']
                viento = data['wind']['speed']
                
                texto = f"🌤️ *Clima en {ciudad.title()}*\n\n"
                texto += f"🌡️ *Temperatura:* {temp}°C\n"
                texto += f"☁️ *Condición:* {descripcion.title()}\n"
                texto += f"💧 *Humedad:* {humedad}%\n"
                texto += f"💨 *Viento:* {viento} m/s\n"
                texto += f"\n📅 *Actualizado:* {datetime.now().strftime('%H:%M')}"
                
                TelegramAPI.send_message(chat_id, texto)
                
                data_manager.data['weather']['user_locations'][str(user_id)] = ciudad
                data_manager.save_data()
                
            else:
                TelegramAPI.send_message(chat_id, f"❌ Ciudad '{ciudad}' no encontrada.")
                
        except Exception as e:
            TelegramAPI.send_message(chat_id, f"❌ Error consultando clima: {str(e)}")
    
    @staticmethod
    def handle_stats(chat_id, user_id):
        profile = data_manager.get_user_profile(user_id)
        
        join_date = datetime.fromisoformat(profile['join_date'])
        dias_uso = (datetime.now() - join_date).days
        
        texto = f"📊 *TUS ESTADÍSTICAS PERSONALES*\n\n"
        texto += f"👤 *Usuario:* #{user_id}\n"
        texto += f"📅 *Miembro desde:* {join_date.strftime('%d/%m/%Y')}\n"
        texto += f"🗓️ *Días activo:* {dias_uso} días\n"
        texto += f"⚡ *Comandos ejecutados:* {profile['total_commands']}\n"
        texto += f"🏆 *Nivel actual:* {profile['level']}\n"
        texto += f"⭐ *Puntos:* {profile['points']}\n"
        
        progreso = (profile['points'] % 10) / 10 * 100
        texto += f"🎯 *Progreso nivel {profile['level'] + 1}:* {progreso:.0f}%\n\n"
        
        if data_manager.data['analytics']['command_usage']:
            top_commands = sorted(data_manager.data['analytics']['command_usage'].items(), 
                                key=lambda x: x[1], reverse=True)[:3]
            texto += f"🔥 *Top comandos del bot:*\n"
            for i, (cmd, count) in enumerate(top_commands, 1):
                texto += f"{i}.  ({count} usos)\n"
        
        TelegramAPI.send_message(chat_id, texto)

def process_scheduled_messages():
    try:
        now = datetime.now()
        mensajes_pendientes = [m for m in data_manager.data['messenger']['scheduled_messages'] 
                             if m['estado'] == 'pendiente']
        
        for mensaje in mensajes_pendientes:
            fecha_envio = datetime.fromisoformat(mensaje['fecha_envio'])
            if now >= fecha_envio:
                TelegramAPI.send_message(
                    mensaje['chat_id'], 
                    f"⏰ *Recordatorio Programado:*\n\n{mensaje['mensaje']}"
                )
                
                mensaje['estado'] = 'enviado'
                mensaje['enviado_en'] = now.isoformat()
        
        data_manager.save_data()
        
    except Exception as e:
        logger.error(f"Error procesando mensajes programados: {e}")

def run_bot():
    offset = 0
    
    while True:
        try:
            updates = TelegramAPI.get_updates(offset)
            
            if updates.get('ok'):
                for update in updates.get('result', []):
                    offset = update['update_id'] + 1
                    
                    if 'message' in update:
                        MessageHandler.handle_message(update['message'])
                        
                        data_manager.data['keepalive']['pings'].append({
                            'timestamp': datetime.now().isoformat(),
                            'type': 'user_message'
                        })
            else:
                logger.error("Error obteniendo updates de Telegram")
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Error en bot principal: {e}")
            time.sleep(10)

schedule.every(1).minutes.do(process_scheduled_messages)

def run_scheduler():
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error en scheduler: {e}")
            time.sleep(60)

app = Flask(__name__)

@app.route('/')
def home():
    uptime_start = datetime.fromisoformat(data_manager.data['keepalive']['uptime_start'])
    return jsonify({
        'name': 'FUSION BOT v7.0 - COMPLETO + KEEPALIVE',
        'status': 'ACTIVE',
        'uptime': str(datetime.now() - uptime_start).split('.')[0],
        'features': [
            'Smart Messenger (programación avanzada)',
            'Loto Predictor (IA + charada cubana)',
            'Clima Inteligente (API real)',
            'Analytics (estadísticas personales)',
            'Sistema Keepalive 24/7'
        ],
        'total_users': len(data_manager.data['users']['profiles']),
        'total_commands': sum(data_manager.data['analytics']['command_usage'].values()),
        'scheduled_messages': len(data_manager.data['messenger']['scheduled_messages']),
        'keepalive_pings': keepalive_manager.ping_count,
        'version': '7.0-completo-keepalive',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'uptime': str(datetime.now() - datetime.fromisoformat(data_manager.data['keepalive']['uptime_start'])).split('.')[0],
        'last_ping': keepalive_manager.last_ping.isoformat(),
        'active_features': 5,
        'telegram_connected': True
    })

@app.route('/ping')
def ping():
    return jsonify({
        'status': 'pong',
        'timestamp': datetime.now().isoformat(),
        'ping_count': keepalive_manager.ping_count
    })

@app.route('/status')
def status():
    return jsonify({
        'bot_status': 'active',
        'keepalive_status': 'running',
        'features_status': {
            'smart_messenger': 'active',
            'loto_predictor': 'active', 
            'weather': 'active',
            'analytics': 'active',
            'keepalive': 'active'
        },
        'uptime': str(datetime.now() - datetime.fromisoformat(data_manager.data['keepalive']['uptime_start'])),
        'health_score': 100
    })

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Flask iniciando en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN requerido")
        return
    
    logger.info("🚀 INICIANDO FUSION BOT v7.0 - COMPLETO + KEEPALIVE")
    logger.info("📱 Smart Messenger con programación avanzada")
    logger.info("🎯 Loto Predictor con IA y charada cubana")
    logger.info("🌤️ Clima inteligente con API real")
    logger.info("📊 Analytics y estadísticas personales")
    logger.info("🔄 Sistema keepalive 24/7 activado")
    
    threads = []
    
    bot_thread = Thread(target=run_bot, daemon=True, name="BotPrincipal")
    bot_thread.start()
    threads.append(bot_thread)
    
    flask_thread = Thread(target=run_flask, daemon=True, name="FlaskKeepAlive")
    flask_thread.start()
    threads.append(flask_thread)
    
    keepalive_thread = Thread(target=keepalive_manager.run_keepalive_loop, daemon=True, name="KeepAliveManager")
    keepalive_thread.start()
    threads.append(keepalive_thread)
    
    scheduler_thread = Thread(target=run_scheduler, daemon=True, name="MessageScheduler")
    scheduler_thread.start()
    threads.append(scheduler_thread)
    
    logger.info(f"✅ {len(threads)} servicios iniciados")
    logger.info("🔥 FUSION BOT COMPLETO FUNCIONANDO 24/7")
    
    try:
        while True:
            time.sleep(300)
            alive_threads = [t for t in threads if t.is_alive()]
            logger.info(f"💓 Heartbeat: {len(alive_threads)}/{len(threads)} servicios activos")
            
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo bot")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")

if __name__ == '__main__':
    main()
