#!/usr/bin/env python3
"""
CONFIGURADOR DE SERVICIOS EXTERNOS DE KEEPALIVE
Script para configurar UptimeRobot, Cron-job.org y otros servicios gratuitos
"""
import requests
import json
import time

class ExternalKeepAliveSetup:
    """Configurar servicios externos de monitoreo"""
    
    def __init__(self, service_url):
        self.service_url = service_url
        
    def setup_uptimerobot_instructions(self):
        """Instrucciones para configurar UptimeRobot"""
        instructions = f"""
🤖 CONFIGURAR UPTIMEROBOT (GRATIS)

1. Ve a: https://uptimerobot.com
2. Crea cuenta gratuita
3. Añade nuevo monitor:
   - Tipo: HTTP(s)
   - URL: {self.service_url}
   - Intervalo: 5 minutos
   - Nombre: "Fusion Bot Keepalive"

4. Añadir monitores adicionales:
   - {self.service_url}/health
   - {self.service_url}/ping
   - {self.service_url}/status

Esto mantendrá tu bot despierto las 24 horas.
"""
        return instructions
    
    def setup_cronjob_instructions(self):
        """Instrucciones para Cron-job.org"""
        instructions = f"""
⏰ CONFIGURAR CRON-JOB.ORG (GRATIS)

1. Ve a: https://cron-job.org
2. Registrate gratis
3. Crear nuevo Cron Job:
   - URL: {self.service_url}/wake
   - Intervalo: Cada 10 minutos
   - Título: "Bot Keepalive"

4. Crear trabajos adicionales:
   - URL: {self.service_url}/ping (cada 15 min)
   - URL: {self.service_url}/health (cada 30 min)

Limite gratuito: 25 trabajos, más que suficiente.
"""
        return instructions
    
    def setup_betteruptime_instructions(self):
        """Instrucciones para Better Uptime"""
        instructions = f"""
📊 CONFIGURAR BETTER UPTIME (GRATIS)

1. Ve a: https://betteruptime.com
2. Plan gratuito incluye monitoreo
3. Añadir nuevo monitor:
   - URL: {self.service_url}
   - Frecuencia: 3 minutos
   - Regiones: Múltiples

Características gratis:
- Monitoreo cada 3 minutos
- Múltiples regiones
- Alertas por email/SMS
"""
        return instructions
    
    def generate_all_instructions(self):
        """Generar todas las instrucciones"""
        return f"""
🚀 GUÍA COMPLETA KEEPALIVE 24/7 PARA TU BOT

Tu URL del servicio: {self.service_url}

{self.setup_uptimerobot_instructions()}

{self.setup_cronjob_instructions()}

{self.setup_betteruptime_instructions()}

🔧 CONFIGURACIÓN ADICIONAL EN RENDER:

1. Variables de entorno necesarias:
   RENDER_SERVICE_URL={self.service_url}
   TELEGRAM_BOT_TOKEN=tu_token_aqui

2. En Render Dashboard:
   - Configura Auto-Deploy desde GitHub
   - Habilita "Auto-Deploy" en "On"
   - Selecciona región más cercana

💡 TIPS PROFESIONALES:

1. Usa múltiples servicios de monitoreo
2. Configura intervalos diferentes (5, 10, 15 min)
3. Monitorea diferentes endpoints
4. Configura alertas por email

🎯 RESULTADO:
Con esta configuración tu bot estará activo 24/7
sin interrupciones en el plan gratuito de Render.

✅ CONFIRMACIÓN:
Una vez configurado, tu bot responderá a comandos
las 24 horas del día sin dormirse jamás.
"""

# Ejecutar para generar instrucciones
if __name__ == "__main__":
    service_url = "https://tu-servicio.onrender.com"  # Cambiar por tu URL real
    setup = ExternalKeepAliveSetup(service_url)
    print(setup.generate_all_instructions())
