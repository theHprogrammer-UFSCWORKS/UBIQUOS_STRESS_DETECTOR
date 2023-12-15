# core/management/commands/startmqtt.py
from django.core.management.base import BaseCommand
from mqtt.mqtt_client import run as mqtt_run

class Command(BaseCommand):
    help = 'Inicia o cliente MQTT'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando o cliente MQTT...'))
        mqtt_run()
