#include <Arduino.h>
#include <DHT.h>
#include <painlessMesh.h>
#include "configs.h"
#include "const.h"
#include "namedMesh.h"

typedef struct Measurements {
  float temperature;
  float humidity;
  float luminosity;
  bool hazardous_gas_warning;
  int number_of_readings;
} Measurements;

// Function prototypes
void meshReceiveCallback(const uint32_t &from, const String &msg);
void meshReceiveNamedCallback(const String &from, const String &msg);
void meshChangeConnCallback();
void resetMeasurements();
String serializeMeasurements(Measurements meas);

// Tasks
Task readSensors;
Task sendMeasurementsToBridge;

// Global variables
Scheduler scheduler;
namedMesh mesh;
Task sendMeasurementsToBridge;
DHT dht(DHT_PIN, DHT_TYPE);
String node_name = NODE_NAME;
String bridge_name = BRIDGE_NAME;
Measurements latest_average_measures;

void setup() {
  // ---- General configs ----
  Serial.begin(BAUD_RATE);
  dht.begin();
  resetMeasurements();

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
  scheduler.addTask(readSensors);
  sendMeasurementsToBridge.enable();
  readSensors.enable();
}

void loop() { mesh.update(); }

Task sendMeasurementsToBridge(TASK_SECOND * 30, TASK_FOREVER, []() {
  String msg = serializeMeasurements(latest_average_measures);
  mesh.sendSingle(bridge_name, msg);
  resetMeasurements();
});

Task readSensors(TASK_SECOND * 5, TASK_FOREVER, []() {
  int n = latest_average_measures.number_of_readings + 1;

  // latest_average_measures.temperature += dht.readTemperature() / n;
  // latest_average_measures.humidity += dht.readHumidity() / n;
  latest_average_measures.temperature += 21;
  latest_average_measures.humidity += 23;
  latest_average_measures.luminosity = 105;
  latest_average_measures.hazardous_gas_warning = false;

  latest_average_measures.number_of_readings = n;
});

void resetMeasurements() {
  latest_average_measures.temperature = 0;
  latest_average_measures.humidity = 0;
  latest_average_measures.luminosity = 0;
  latest_average_measures.hazardous_gas_warning = false;
  latest_average_measures.number_of_readings = 0;
}

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
  Log(DEBUG, "Received message from %u, msg: %s\n", from, msg.c_str());
}

void meshReceiveNamedCallback(const String &from, const String &msg) {
  Log(DEBUG, "Received message from %u, msg: %s\n", from, msg.c_str());
}

void meshChangeConnCallback() { Log(DEBUG, "Changed connections!\n"); }
