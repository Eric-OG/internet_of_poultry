#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>
#include <painlessMesh.h>
#include "ChickenUDP.h"
#include "configs.h"
#include "namedMesh.h"
#include "secrets.h"

// Function prototypes
void meshReceiveCallback(const uint32_t &from, const String &msg);
void meshChangeConnCallback();
void mqttReceiveCallback(char *topic, uint8_t *payload, unsigned int length);
void checkNetworkChange();
String serialize_topology();
void publish_topology();
void ack_connection();

// Global variables
IPAddress bridge_IP(0, 0, 0, 0);
WiFiClientSecure net = WiFiClientSecure();
PubSubClient mqttClient(net);
namedMesh mesh;
String node_name = BRIDGE_NAME;
ChickenUDP cudp;

void setup() {
  // ---- General configs ----
  Serial.begin(BAUD_RATE);

  // ---- Mqtt client configs ----
  mqttClient.setCallback(&mqttReceiveCallback);

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
  mesh.onChangedConnections(&publish_topology);
  mesh.onNewNamedConnection(&publish_topology);
}

void loop() {
  mesh.update();
  mqttClient.loop();
  checkNetworkChange();
}

void checkNetworkChange() {
  IPAddress current_local_ip = IPAddress(mesh.getStationIP());

  if (bridge_IP != current_local_ip) {
    bridge_IP = current_local_ip;

    net.setCACert(AWS_ROOT_CA);
    net.setCertificate(AWS_DEVICE_CERT);
    net.setPrivateKey(AWS_PRIVATE_KEY);
    mqttClient.setServer(AWS_IOT_ENDPOINT, 8883);

    String msg = "Ready! Bridge local IP is " + bridge_IP.toString() + "\n";
    Log(DEBUG, msg.c_str());

    if (mqttClient.connect(THING_NAME)) {
      mqttClient.subscribe(DASH_ROOT_TOPIC);
      ack_connection();
      publish_topology();
    }
  }
}

void meshReceiveCallback(const uint32_t &from, const String &msg) {
  JsonObject app_data;
  String from_node_name = mesh.getNameById(from);
  Log(DEBUG, "Received message from %s, msg: %s \n", from_node_name.c_str(), msg.c_str());

  bool unpack_successful = cudp.unpackData(msg, &app_data);
  if (!unpack_successful) {
    Log(ERROR, "Package discarded due to CUDP CRC check\n");
    return;
  }

  app_data["node_id"] = from;
  app_data["node_name"] = from_node_name;
  short message_type = app_data["msg_type"];

  if (message_type == MEASUREMENTS) {
    String app_data_str;
    serializeJson(app_data, app_data_str);
    mqttClient.publish(MEASUREMENTS_TOPIC, app_data_str.c_str());
  }
}

void mqttReceiveCallback(char *topic, uint8_t *payload, unsigned int length) {
  char *cleanPayload = (char *)malloc(length + 1);
  memcpy(cleanPayload, payload, length);
  cleanPayload[length] = '\0';
  String msg = String(cleanPayload);
  free(cleanPayload);

  Log(DEBUG, "MQTT message received: %s \n", msg);
  String topic_str = String(topic);
  if (topic_str == CONN_CHECK_TOPIC) {
    ack_connection();
  } else if (topic_str == TOPOLOGY_REQUEST) {
    publish_topology();
  }
}

void publish_topology() {
  String topology_json = serialize_topology();
  mqttClient.publish(TOPOLOGY_RESPONSE, topology_json.c_str());
  Log(DEBUG, "Mesh topology is: %s \n", topology_json.c_str());
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

void ack_connection() {
  mqttClient.publish(CONN_ACK_TOPIC, "{\"mesh_name\":\"" MESH_NAME
                                     "\",\"mesh_network\":\"" AP_SSID "\"}");
}