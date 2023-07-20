#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <painlessMesh.h>
#include "configs.h"
#include "const.h"
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
IPAddress bridge_IP(0, 0, 0, 0);
WiFiClient wifiClient;
PubSubClient mqttClient(MQTT_BROKER, MQTT_PORT, mqttReceiveCallback, wifiClient);
namedMesh mesh;
String node_name = BRIDGE_NAME;

void setup() {
  // ---- Serial configs ----
  Serial.begin(BAUD_RATE);

  // ---- Mesh configs ----
  mesh.setDebugMsgTypes(ERROR | DEBUG | CONNECTION | COMMUNICATION | REMOTE);
  // Use the same channel for mesh and for network (AP_SSID)
  mesh.init(MESH_NAME, MESH_PASSWORD, MESH_PORT, WIFI_AP_STA, MESH_CHANNEL);
  mesh.stationManual(AP_SSID, AP_PASSWORD);
  mesh.setHostname(BRIDGE_NAME);
  mesh.setRoot(true);          // Bridge node, should (in most cases) be a root node.
  mesh.setContainsRoot(true);  // All nodes should know that the mesh contains a root
  mesh.setName(node_name);
  // ---- Mesh functions ----
  mesh.onReceive(&meshReceiveCallback);
  mesh.onChangedConnections(&meshChangeConnCallback);
}

void loop() {
  mesh.update();
  mqttClient.loop();
  checkIpChange();
}

void checkIpChange() {
  IPAddress current_local_ip = getlocalIP();

  if (bridge_IP != current_local_ip) {
    bridge_IP = current_local_ip;
    Log(DEBUG, "Bridge local IP is %s \n", bridge_IP.toString());

    if (mqttClient.connect(MESH_NAME)) {
      if (MQTT_DEBUG) {
        String msg = "Ready! Bridge local IP is %s" + bridge_IP.toString();
        mqttClient.publish(DEBUG_TOPIC, "Ready! Bridge local IP is %s \n",
                           bridge_IP.toString());
      }

      mqttClient.subscribe(TOPOLOGY_REQUEST);
      publish_topology();
    }
  }
}

IPAddress getlocalIP() { return IPAddress(mesh.getStationIP()); }

void meshReceiveCallback(const uint32_t &from, const String &msg) {
  StaticJsonDocument<256> doc;
  deserializeJson(doc, msg);
  doc["nodeId"] = from;

  uint32_t message_type = doc["msg_type"];
  if (message_type == MEASUREMENTS) {
    mqttClient.publish(MEASUREMENTS_TOPIC, (doc.as<String>()).c_str());
  }

  Log(DEBUG, "Received message from %u, msg: %s\n", from, msg.c_str());
  mqttClient.publish(MEASUREMENTS_TOPIC, msg.c_str());
}

void meshChangeConnCallback() { publish_topology(); }

void mqttReceiveCallback(char *topic, uint8_t *payload, unsigned int length) {
  Log(DEBUG, "MQTT message received: %s \n", String(*payload));

  if (String(topic) == String(TOPOLOGY_REQUEST)) {
    publish_topology();
  }
}

void publish_topology() {
  String topology_json = jsonify_topology();
  mqttClient.publish(TOPOLOGY_RESPONSE, topology_json.c_str());
  Log(DEBUG, "Mesh topology is: %s \n", topology_json);
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