// Bibliotecas
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Timer/Interrupção
hw_timer_t * sampleTimer = NULL;
portMUX_TYPE sampleTimerMux = portMUX_INITIALIZER_UNLOCKED;

#define USE_ARDUINO_INTERRUPTS true
//#define NO_PULSE_SENSOR_SERIAL true
#include <PulseSensorPlayground.h>

// Pinagem
#define GSR_PIN 34
const int oneWireBus = 4;

// Variáveis
bool iniciarColeta = false;
String macAddress; // Variável para armazenar o endereço MAC
float temperatura = 0;
int gsrReading = 0;
float gsrResistance = 0;
int freqCardiaca = 0;
unsigned long start = 0;


// Credenciais de rede
const char* ssid = "ssid";
const char* password = "password";

// Credenciais do broker
const char* mqtt_server = "IP_DE_CONEXÃO";
const int mqtt_port = 1883;
const char* mqtt_topic_pub = "esp32/sensores/dados";
const char* mqtt_topic_sub = "esp32/sensores/comandos";

// Instancializações
WiFiClient espClient;
PubSubClient client(espClient);
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

PulseSensorPlayground pulseSensor;
const int PULSE_INPUT = A0;
const int PULSE_BLINK = 13;
const int PULSE_FADE = 5;
const int PULSE_THRESHOLD = 1900;

void IRAM_ATTR onSampleTime() {
  portENTER_CRITICAL_ISR(&sampleTimerMux);
  PulseSensorPlayground::OurThis->onSampleTime();
  portEXIT_CRITICAL_ISR(&sampleTimerMux);
}

void setup_wifi() {
  delay(10);
  // Conectando à rede Wi-Fi
  Serial.println("Conectando à rede Wi-Fi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Conectado à rede Wi-Fi");
  Serial.println("Endereço IP: " + WiFi.localIP().toString());

  macAddress = WiFi.macAddress(); // Obter o endereço MAC do ESP32
  Serial.println("Endereço MAC: " + macAddress);
}

void reconnect() {
  // Loop até estarmos reconectados
  while (!client.connected()) {
    //    Serial.print("Tentando conexão MQTT...");
    // Tente conectar
    if (client.connect("ESP32Client")) {
      Serial.println("conectado");

      client.subscribe(mqtt_topic_sub); // Inscrever-se no tópico de comandos
    } else {
      Serial.print("falhou, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5 segundos");
      // Espere 5 segundos antes de tentar novamente
      unsigned long startAttemptTime = millis();
      while (millis() - startAttemptTime < 5000) {
        delay(0);
      }
    }
  }
}

// Protótipo da função de callback
void callback(char* topic, byte* payload, unsigned int length);
void callback(char* topic, byte* payload, unsigned int length) {
  // Convertendo payload para string
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // Verificar se a mensagem recebida contém o endereço MAC
  if (message == macAddress) {
    iniciarColeta = true;
  } else {
    // Mensagem recebida não é o que estamos esperando
    Serial.println("Mensagem recebida não corresponde ao MAC esperado.");
  }
}

void setup() {
  Serial.begin(115200);

  setup_wifi();
  analogReadResolution(12);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  pinMode(GSR_PIN, INPUT);
  sensors.begin();
  pulseSensor.analogInput(PULSE_INPUT);
  pulseSensor.blinkOnPulse(PULSE_BLINK);
  pulseSensor.fadeOnPulse(PULSE_FADE);
  pulseSensor.setSerial(Serial);
  pulseSensor.setThreshold(PULSE_THRESHOLD);

  if (!pulseSensor.begin()) {
    while (1) {
      digitalWrite(PULSE_BLINK, LOW);
      delay(50);
      digitalWrite(PULSE_BLINK, HIGH);
      delay(50);
    }
  }
  if (!pulseSensor.begin()) {
    Serial.println("Could not find a valid PulseSensor.");
  }

  sampleTimer = timerBegin(0, 80, true);
  timerAttachInterrupt(sampleTimer, &onSampleTime, true);
  timerAlarmWrite(sampleTimer, 3000, true);
  timerAlarmEnable(sampleTimer);
}

void loop() {
  static unsigned long lastTime = 0; // Armazenar a última vez que os dados foram enviados
  unsigned long currentTime = millis();

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  if (iniciarColeta) {
    if (start == 0) { // Iniciar o temporizador quando a coleta começar
      start = currentTime;
    }

    if (currentTime - lastTime >= 2000) { // Verifica se 5 segundos se passaram
      if (pulseSensor.sawStartOfBeat()) {
        sensors.requestTemperatures();
        freqCardiaca = pulseSensor.getBeatsPerMinute();
        temperatura = sensors.getTempCByIndex(0);
        gsrReading = analogRead(GSR_PIN); // Lê o valor analógico do sensor GSR
        gsrResistance = (4095.0 + 2 * gsrReading) * 10000 / (4095.0 - gsrReading); // Calcula a resistência da pele

        StaticJsonDocument<200> doc;
        doc["gsr"] = gsrResistance;
        doc["freq_cardiaca"] = freqCardiaca;
        doc["temperatura"] = temperatura;
        doc["coleta_ativa"] = "True";

        String dadosJson;
        serializeJson(doc, dadosJson);
        client.publish(mqtt_topic_pub, dadosJson.c_str());
        Serial.println("Dados publicados: " + dadosJson);

        lastTime = currentTime; // Atualiza o último tempo de envio
      }
    }

    // Verifica se já passou 1 minuto desde o início da coleta
    if (currentTime - start >= 60000 && iniciarColeta) {
      if (pulseSensor.sawStartOfBeat()) {
        freqCardiaca = pulseSensor.getBeatsPerMinute();
        temperatura = sensors.getTempCByIndex(0);
        gsrReading = analogRead(GSR_PIN); // Lê o valor analógico do sensor GSR
        gsrResistance = (4095.0 + 2 * gsrReading) * 10000 / (4095.0 - gsrReading); // Calcula a resistência da pele

        // Enviar a última mensagem com coleta_ativa como false
        StaticJsonDocument<200> docFinal;
        docFinal["gsr"] = gsrResistance;
        docFinal["freq_cardiaca"] = freqCardiaca;
        docFinal["temperatura"] = temperatura;
        docFinal["coleta_ativa"] = "False";

        String mensagemFinal;
        serializeJson(docFinal, mensagemFinal);
        client.publish(mqtt_topic_pub, mensagemFinal.c_str());
        Serial.println("Mensagem final de coleta enviada: " + mensagemFinal);

        iniciarColeta = false;
        start = 0; // Reseta o start para a próxima coleta
      }
    }
  } else {
    // Espera 5 segundos antes da próxima iteração
    if (currentTime - lastTime >= 3000) {
      Serial.println("Aguardando comando para iniciar análise...");
      lastTime = currentTime;
    }
  }
}
