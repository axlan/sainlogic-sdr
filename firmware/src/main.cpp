#include <Arduino.h>
#include <ESP8266WiFi.h>

#include <ESP8266TimerInterrupt.h>
#include <PubSubClient.h>

#include "ring_buffer.h"
#include "ppm_tracker.h"
#include "secrets.h"

// Define DEBUG_SAMPLER to log data packets to serial
// Instead of normal operation


// D1 GPIO5
// Connects to pin that goes low during receive
#define PIN_IN1 5
// D2 GPIO4
// Connects to pin that outputs received data
#define PIN_IN2 4

// Target time between samples
// Must be long enough that MCU can keep up with
// Expected samples/symbol = is SLEEP_US/46.3uS
#define SAMPLE_PERIOD_US 40

// Parameters for synching data
#define MIN_SAMPLES 4
#define MAX_SAMPLES 16

// MQTT Broker to connect to
const char* mqtt_server = "192.168.1.110";

WiFiClient wifi_client;
PubSubClient client(wifi_client);

// Init ESP8266 timer
ESP8266Timer ITimer;

BinaryPpmTracker tracker(MIN_SAMPLES, MAX_SAMPLES);

// setup WiFi based on ssid and password
// defined in gitignored secrets.h
void setup_wifi() {

  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Don't listen for any MQTT topics
void callback(char* topic, byte* payload, unsigned int length) {

}

// Reconnect to MQTT Broker
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...1");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


// Setup pins, serial, timer ISR, Wifi, and MQTT
void setup() {
  pinMode(PIN_IN1, INPUT);
  pinMode(PIN_IN2, INPUT);
  set_sample_pin(PIN_IN2);
  Serial.begin(115200);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  //client.setSocketTimeout(0xFFFF);
  client.setKeepAlive(0xFFFF);

  if (ITimer.attachInterruptInterval(SAMPLE_PERIOD_US, sample_input))
    Serial.println("Starting  ITimer OK, millis() = " + String(millis()));
  else
    Serial.println("Can't set ITimer. Select another freq. or interval");
}

#ifdef DEBUG_SAMPLER
// When debugging, log bit sequence following sample going low
void debug_loop() {
  static bool sent = true;
  if (sent) {
    if (!digitalRead(PIN_IN1)) {
      reset_sampler();
      sent = false;
    }
    return;
  }
  size_t buffered_len = num_samples();
  if (buffered_len == SAMPLE_LEN - 1) {
    sent = true;
    for (int i = 0; i < SAMPLE_LEN/8; i++){
      Serial.printf("%02X", get_sample_buffer()[i]);
    }
    Serial.print("\n");
    reset_sampler();
  }
}
#endif

void loop() {
  #ifdef DEBUG_SAMPLER
  debug_loop();
  #else
  size_t buffered_len = num_samples();
  if (buffered_len > SAMPLE_LEN / 2) {
    Serial.printf("Fell Behind\n");
    reset_sampler();
    return;
  }
  for (size_t i = 0; i < buffered_len; i++) {
    // Demodulate PPM signal
    tracker.process_sample(get_next_sample());

    // // Used for debugging
    // size_t last_count = 0;
    // if (last_count > 0 && tracker.cur_rx_len() == 0) {
    //   Serial.printf("%lu %u\n", millis(), last_count);
    // }
    // last_count = tracker.cur_rx_len();

    // If full message is received publish it and reset tracker
    if (tracker.cur_rx_len() == MSG_LEN) {
      for (int i = 0; i < MSG_LEN/8; i++){
        Serial.printf("%02X", tracker.get_msg()[i]);
      }
      Serial.print("\n");

      if (!client.connected()) {
        reconnect();
      }
      client.publish("weather_data", tracker.get_msg(), MSG_LEN/8);
      client.loop();
      reset_sampler();
      tracker.reset();
    }
  }
  delayMicroseconds(SAMPLE_PERIOD_US * 10);
  #endif
}
