# mqtt_client.py

import json
from paho.mqtt import client as mqtt_client
from apps.home.models import Analise, DadoSensor

# Configurações do broker MQTT
broker = 'localhost'
port = 1883
topic_sub = "esp32/sensores/dados"  # Tópico para se inscrever e receber comandos
topic_pub = "esp32/sensores/comandos"    # Tópico para publicar dados
client_id = 'django_mqtt_client_1'
username = 'admin'
password = 'admin'

# Função callback chamada quando o cliente recebe uma resposta CONNACK do servidor.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao MQTT Broker!")
        client.subscribe(topic_sub)  # Se inscreve no tópico de comandos
    else:
        print("Falha na conexão, retorno do código %d\n", rc)

def on_message(client, userdata, msg):
    try:
        print(f"Mensagem recebida `{msg.payload.decode()}` do tópico `{msg.topic}`")
        data = json.loads(msg.payload.decode())


        nova_analise = Analise.objects.last()
        novo_dado = DadoSensor(analise=nova_analise, 
                                gsr_media=data['gsr'], 
                                freq_cardiaca_media=data['freq_cardiaca'], 
                                temperatura_final=data['temperatura'],
                                coleta_ativa=data['coleta_ativa'])
        novo_dado.save()

    except json.JSONDecodeError:
        print("Payload não é um JSON válido, tratando como string simples.")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

    
    # Função para publicar uma mensagem no tópico de dados (caso necessário)
def publish_message(client, message):
    client.publish(topic_pub, json.dumps(message))

def connect_mqtt():
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    return client

def run():
    client = connect_mqtt()
    client.loop_forever()  # Inicia o loop para processar callbacks.

if __name__ == '__main__':
    run()
