#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFiClient.h>
#include <painlessMesh.h>
#include "configs.h"
#include "namedMesh.h"

// Function prototypes
void receivedCallback(const uint32_t &from, const String &msg);
void mqttCallback(char *topic, byte *payload, unsigned int length);
void checkIpChange();
IPAddress getlocalIP();

// Global variables
IPAddress myIP(0, 0, 0, 0);
WiFiClient wifiClient;
PubSubClient mqttClient(MQTT_BROKER, MQTT_PORT, mqttCallback, wifiClient);
namedMesh mesh;

void setup() {
  // ---- Serial configs ----
  Serial.begin(BAUD_RATE);

  // ---- Mesh configs ----
  mesh.setDebugMsgTypes(ERROR | DEBUG | CONNECTION | COMMUNICATION | REMOTE);
  // Use the same channel for mesh and for network (AP_SSID)
  mesh.init(MESH_NAME, MESH_PASSWORD, MESH_PORT, WIFI_AP_STA, MESH_CHANNEL);
  mesh.onReceive(&receivedCallback);
  mesh.stationManual(AP_SSID, AP_PASSWORD);
  mesh.setHostname(NODE_NAME);
  // Bridge node, should (in most cases) be a root node.
  mesh.setRoot(true);
  // All nodes should know that the mesh contains a root
  mesh.setContainsRoot(true);

  Serial.println("Name is " + String(NODE_NAME));
}

void loop() {
  mesh.update();
  mqttClient.loop();
  checkIpChange();
}

void receivedCallback(const uint32_t &from, const String &msg) {
  Serial.printf("bridge: Received from %u msg=%s\n", from, msg.c_str());
  mqttClient.publish(DEBUG_TOPIC, msg.c_str());
}

void checkIpChange() {
  IPAddress current_local_ip = getlocalIP();

  if (myIP != current_local_ip) {
    myIP = current_local_ip;
    Serial.println("My IP is " + myIP.toString());

    if (mqttClient.connect(MESH_NAME)) {
      mqttClient.publish(DEBUG_TOPIC, "Ready!");
    }
  }
}

IPAddress getlocalIP() { return IPAddress(mesh.getStationIP()); }

void mqttCallback(char *topic, uint8_t *payload, unsigned int length) {
  Serial.printf("MQTT message received");
}
