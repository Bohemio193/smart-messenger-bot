#!/usr/bin/env python3
"""
CONFIGURACIÓN AUTOMÁTICA DE KEEPALIVE
Script para automatizar la configuración de servicios externos
"""
import requests
import json
import os

def auto_configure_keepalive():
    """Configuración automática básica"""
    
    service_url = os.environ.get('RENDER_SERVICE_URL', 'https://your-service.onrender.com')
    
    print(f"🚀 Configurando keepalive para: {service_url}")
    
    # Test de endpoints
    endpoints = ['/', '/health', '/ping', '/status']
    
    for endpoint in endpoints:
        url = f"{service_url}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: Error - {e}")
    
    print("\n🔧 Para completar la configuración:")
    print("1. Configura UptimeRobot en: https://uptimerobot.com")
    print("2. Añade Cron Jobs en: https://cron-job.org")
    print("3. Monitoreo adicional en: https://betteruptime.com")
    print(f"\n📍 Tu URL de servicio: {service_url}")

if __name__ == "__main__":
    auto_configure_keepalive()
