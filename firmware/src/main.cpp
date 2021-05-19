#include <Arduino.h>
#include <ESP8266WiFi.h>

#include <PubSubClient.h>

#include "secrets.h"

// D1 GPIO5
#define PIN_IN1 5
// D2 GPIO4
#define PIN_IN2 4

#define SLEEP_US 50

#define BIT_SET(a,b) ((a) |= (1ULL<<(b)))
#define BIT_CLEAR(a,b) ((a) &= ~(1ULL<<(b)))

#define MIN_SAMPLES 2
#define MAX_SAMPLES 10

#define MSG_LEN 128

//#define DEBUG_SAMPLER

const char* mqtt_server = "192.168.1.110";

WiFiClient wifi_client;
PubSubClient client(wifi_client);

class BinaryPpmTracker {
 public:
  BinaryPpmTracker() : last_sample(false) {
    reset();
  }

  void process_sample(bool sample) {
    if (cur_idx == MSG_LEN) {
      return;
    }
    if (sample != last_sample) {
      if (repetitions > MIN_SAMPLES) {
        if (!edge) {
            set_bit();
            cur_idx++;
        }
        edge = !edge;
        repetitions = 0;
      } else {
        reset();
      }
    } else {
      repetitions++;
      if (cur_idx > 0 and repetitions > MAX_SAMPLES) {
        if (!edge) {
            reset();
        }
        else {
          edge = false;
          repetitions = 0;
        }
      }
    }
    last_sample = sample;
  }

  void reset() {
    cur_idx = 0;
    edge = 0;
    repetitions = 0;
  }

  int cur_rx_len() const {
    return cur_idx;
  }

  const uint8_t *get_msg() const {
    return rx_data;
  }

 private:

  void set_bit() {
    int bit_idx = 7 - cur_idx % 8;
    int byte_idx = cur_idx / 8;
    if(last_sample) {
      BIT_SET(rx_data[byte_idx], bit_idx);
    } else {
      BIT_CLEAR(rx_data[byte_idx], bit_idx);
    }
  }

  int cur_idx;
  bool edge;
  bool last_sample;
  int repetitions;
  uint8_t rx_data[MSG_LEN/8];
};

BinaryPpmTracker tracker;


int last_count = 0;
unsigned long last_update = 0;
bool slept = true;


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


void callback(char* topic, byte* payload, unsigned int length) {

}

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

void setup() {
  pinMode(PIN_IN1, INPUT);
  pinMode(PIN_IN2, INPUT);
  Serial.begin(115200);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  //client.setSocketTimeout(0xFFFF);
  client.setKeepAlive(0xFFFF);
}

#ifdef DEBUG_SAMPLER
#define SAMPLE_LEN 10240
uint8_t samples[SAMPLE_LEN/8];
int idx = 0;
#endif

void loop() {
  unsigned long update = micros();
  if (update > last_update && update < last_update + SLEEP_US ) {
    slept = true;
    return;
  }
  #ifdef DEBUG_SAMPLER
  if (!slept) {
    Serial.printf("!\n");
    update = micros();
  }
  slept = false;
  #endif
  last_update = update;

  #ifdef DEBUG_SAMPLER
  if (idx ==0 && digitalRead(PIN_IN1)) {
    return;
  }
  int bit_idx = idx % 8;
  int byte_idx = idx / 8;
  if(digitalRead(PIN_IN2)) {
    BIT_SET(samples[byte_idx], bit_idx);
  } else {
    BIT_CLEAR(samples[byte_idx], bit_idx);
  }

  idx++;
  if (idx == SAMPLE_LEN) {
    for (int i = 0; i < SAMPLE_LEN/8; i++){
      Serial.printf("%02X", samples[i]);
    }
    Serial.print("\n");
    idx = 0;
    delay(1000);
  }
  #endif


  tracker.process_sample(digitalRead(PIN_IN2));
  // if (last_count > 0 && tracker.cur_rx_len() == 0) {
  //   Serial.printf("%d\n", last_count);
  // }
  // last_count = tracker.cur_rx_len();
  if (tracker.cur_rx_len() == MSG_LEN) {
    #ifndef DEBUG_SAMPLER
    for (int i = 0; i < MSG_LEN/8; i++){
      Serial.printf("%02X", tracker.get_msg()[i]);
    }
    Serial.print("\n");

    if (!client.connected()) {
      reconnect();
    }
    client.publish("weather_data", tracker.get_msg(), MSG_LEN/8);
    client.loop();
    #endif
    tracker.reset();
  }
}
