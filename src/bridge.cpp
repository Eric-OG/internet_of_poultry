#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFiClient.h>
#include <painlessMesh.h>
#include "configs.h"
#include "namedMesh.h"

// Function prototypes
void meshReceiveCallback(const uint32_t &from, const String &msg);
void meshChangeConnCallback();
void mqttReceiveCallback(char *topic, byte *payload, unsigned int length);
void checkIpChange();
IPAddress getlocalIP();
String jsonify_topology();
void publish_topology();

// Global variables
IPAddress myIP(0, 0, 0, 0);
WiFiClient wifiClient;
PubSubClient mqttClient(MQTT_BROKER, MQTT_PORT, mqttReceiveCallback, wifiClient);
namedMesh mesh;
String node_name = NODE_NAME;

void setup() {
  // ---- Serial configs ----
  Serial.begin(BAUD_RATE);

  // ---- Mesh configs ----
  mesh.setDebugMsgTypes(ERROR | DEBUG | CONNECTION | COMMUNICATION | REMOTE);
  // Use the same channel for mesh and for network (AP_SSID)
  mesh.init(MESH_NAME, MESH_PASSWORD, MESH_PORT, WIFI_AP_STA, MESH_CHANNEL);
  mesh.onReceive(&meshReceiveCallback);
  mesh.onChangedConnections(&meshChangeConnCallback);
  mesh.stationManual(AP_SSID, AP_PASSWORD);
  mesh.setHostname(NODE_NAME);
  mesh.setRoot(true);          // Bridge node, should (in most cases) be a root node.
  mesh.setContainsRoot(true);  // All nodes should know that the mesh contains a root
  mesh.setName(node_name);
}

void loop() {
  mesh.update();
  mqttClient.loop();
  checkIpChange();
}

void checkIpChange() {
  IPAddress current_local_ip = getlocalIP();

  if (myIP != current_local_ip) {
    myIP = current_local_ip;
    Serial.println("My IP is " + myIP.toString());

    if (mqttClient.connect(MESH_NAME)) {
      mqttClient.publish(DEBUG_TOPIC, "Ready!");
      publish_topology();
      mqttClient.subscribe(TOPOLOGY_REQUEST);
    }
  }
}

IPAddress getlocalIP() { return IPAddress(mesh.getStationIP()); }

void meshReceiveCallback(const uint32_t &from, const String &msg) {
  Serial.printf("Received message from %u msg=%s\n", from, msg.c_str());
  mqttClient.publish(DEBUG_TOPIC, msg.c_str());
}

void meshChangeConnCallback() { publish_topology(); }

void mqttReceiveCallback(char *topic, uint8_t *payload, unsigned int length) {
  Serial.println("MQTT message received");
  Serial.println("topic is: " + String(topic));

  if (String(topic) == String(TOPOLOGY_REQUEST)) {
    publish_topology();
  }
}

void publish_topology() {
  String topology_json = jsonify_topology();
  Serial.println(topology_json);
  mqttClient.publish(TOPOLOGY_RESPONSE, topology_json.c_str());
}

String jsonify_topology() {
  DynamicJsonDocument root_doc(2048);
  JsonObject mesh_tree = root_doc.createNestedObject("mesh_tree");
  JsonObject name_map = root_doc.createNestedObject("name_map");

  DynamicJsonDocument tree_doc(1024);
  deserializeJson(tree_doc, mesh.subConnectionJson());
  mesh_tree.set(tree_doc.as<JsonObject>());

  JsonObject name_map_json = mesh.addressToNameJson();
  name_map.set(name_map_json);

  return root_doc.as<String>();
}