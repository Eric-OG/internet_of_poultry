#include <Arduino.h>
#include <painlessMesh.h>
#include "configs.h"
#include "const.h"
#include "namedMesh.h"

typedef struct Measurements {
  float temperature;
  float humidity;
  float luminosity;
  bool hazardous_gas_warning;
} Measurements;

// Function prototypes
void meshReceiveCallback(const uint32_t &from, const String &msg);
void meshReceiveNamedCallback(const String &from, const String &msg);
void meshChangeConnCallback();
Measurements readSensors();
String serializeMeasurements(Measurements meas);

// Global variables
Scheduler scheduler;
namedMesh mesh;
Task sendMeasurementsToBridge;
String node_name = NODE_NAME;
String bridge_name = BRIDGE_NAME;

void setup() {
  // ---- Serial configs ----
  Serial.begin(BAUD_RATE);

  // ---- Mesh configs ----
  mesh.setDebugMsgTypes(ERROR | DEBUG | CONNECTION | COMMUNICATION | REMOTE);
  mesh.init(MESH_NAME, MESH_PASSWORD, &scheduler, MESH_PORT, WIFI_AP_STA, MESH_CHANNEL);
  mesh.setContainsRoot(true);  // All nodes should know that the mesh contains a root
  mesh.setName(node_name);
  // ---- Mesh functions ----
  mesh.onReceive(&meshReceiveCallback);
  mesh.onReceive(&meshReceiveNamedCallback);
  mesh.onChangedConnections(&meshChangeConnCallback);

  // ---- Tasks configs ----
  scheduler.addTask(sendMeasurementsToBridge);
  sendMeasurementsToBridge.enable();
}

void loop() { mesh.update(); }

Task sendMeasurementsToBridge(TASK_SECOND * 10, TASK_FOREVER, []() {
  Measurements meas = readSensors();
  String msg = serializeMeasurements(meas);
  mesh.sendSingle(bridge_name, msg);
});

Measurements readSensors() {
  Measurements meas;
  meas.temperature = 23.1;
  meas.humidity = 82.3;
  meas.luminosity = 103.0;
  meas.hazardous_gas_warning = false;
  return meas;
};

String serializeMeasurements(Measurements meas) {
  StaticJsonDocument<256> doc;
  JsonObject data = doc.createNestedObject("data");
  data["temperature"] = meas.temperature;
  data["humidity"] = meas.humidity;
  data["luminosity"] = meas.luminosity;
  data["hazardous_gas_warning"] = meas.hazardous_gas_warning;
  doc["msg_type"] = MEASUREMENTS;
  return doc.as<String>();
}

void meshReceiveCallback(const uint32_t &from, const String &msg) {
  DEBUG &&Serial.printf("Received message from %u, msg: %s\n", from, msg.c_str());
}

void meshReceiveNamedCallback(const String &from, const String &msg) {
  DEBUG &&Serial.printf("Received message from %u, msg: %s\n", from, msg.c_str());
}

void meshChangeConnCallback() { DEBUG &&Serial.printf("Changed connection\n"); }
