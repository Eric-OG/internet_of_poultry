#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFiClient.h>
#include <painlessMesh.h>
#include "configs.h"
#include "const.h"
#include "cudp.h"
#include "namedMesh.h"

// Function prototypes
void meshReceiveCallback(const uint32_t &from, const String &msg);
void meshChangeConnCallback();
void mqttReceiveCallback(char *topic, uint8_t *payload, unsigned int length);
void checkIpChange();
void publish_measurements(const uint32_t &origin, JsonObject *app_data);
String serialize_topology();
void publish_topology();

// Global variables
IPAddress bridge_IP(0, 0, 0, 0);
WiFiClient wifiClient;
PubSubClient mqttClient(MQTT_BROKER, MQTT_PORT, mqttReceiveCallback, wifiClient);
namedMesh mesh;
String node_name = BRIDGE_NAME;
CUDP cudp;

void setup() {
  // ---- General configs ----
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
  IPAddress current_local_ip = IPAddress(mesh.getStationIP());

  if (bridge_IP != current_local_ip) {
    bridge_IP = current_local_ip;
    String msg = "Ready! Bridge local IP is %s" + bridge_IP.toString();
    Log(DEBUG, msg.c_str());

    if (mqttClient.connect(MESH_NAME)) {
      if (MQTT_DEBUG) mqttClient.publish(DEBUG_TOPIC, msg.c_str());

      mqttClient.subscribe(TOPOLOGY_REQUEST);
      publish_topology();
    }
  }
}

void meshReceiveCallback(const uint32_t &from, const String &msg) {
  JsonObject app_data;
  Log(DEBUG, "Received message from %u, msg: %s \n", from, msg.c_str());

  bool unpack_successful = cudp.unpackData(msg, &app_data);
  if (!unpack_successful) Log(DEBUG, "Package discarded due to CUDP CRC check\n");

  short message_type = app_data["msg_type"];
  if (message_type == MEASUREMENTS) publish_measurements(from, &app_data);
}

void meshChangeConnCallback() { publish_topology(); }

void mqttReceiveCallback(char *topic, uint8_t *payload, unsigned int length) {
  char *cleanPayload = (char *)malloc(length + 1);
  memcpy(cleanPayload, payload, length);
  cleanPayload[length] = '\0';
  String msg = String(cleanPayload);
  free(cleanPayload);

  Log(DEBUG, "MQTT message received: %s \n", msg);
  if (String(topic) == TOPOLOGY_REQUEST) {
    publish_topology();
  }
}

void publish_measurements(const uint32_t &origin, JsonObject *app_data) {
  String app_data_str;
  (*app_data)["nodeId"] = origin;
  serializeJson(*app_data, app_data_str);
  mqttClient.publish(MEASUREMENTS_TOPIC, app_data_str.c_str());
}

void publish_topology() {
  String topology_json = serialize_topology();
  mqttClient.publish(TOPOLOGY_RESPONSE, topology_json.c_str());
  Log(DEBUG, "Mesh topology is: %s \n", topology_json);
}

String serialize_topology() {
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