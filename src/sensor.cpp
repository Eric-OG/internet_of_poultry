#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <painlessMesh.h>
#include "configs.h"
#include "const.h"
#include "cudp.h"
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
void sendAppData(JsonObject app_data, String destination);
void readSensors();
void sendMeasurementsToBridge();
JsonObject serializeMeasurements(Measurements meas);

// Tasks
Task readSensorsTask(TASK_SECOND * 10, TASK_FOREVER, &readSensors);
Task sendMeasurementsTask(TASK_SECOND * 30, TASK_FOREVER, &sendMeasurementsToBridge);

// Global variables
Scheduler scheduler;
namedMesh mesh;
DHT dht(DHT_PIN, DHT_TYPE);
String node_name = NODE_NAME;
String bridge_name = BRIDGE_NAME;
Measurements latest_average_measures;
CUDP cudp;

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
  scheduler.addTask(readSensorsTask);
  scheduler.addTask(sendMeasurementsTask);
  readSensorsTask.enable();
  sendMeasurementsTask.enable();
}

void loop() { mesh.update(); }

void meshReceiveCallback(const uint32_t &from, const String &msg) {
  Log(DEBUG, "Received message from %u, msg: %s\n", from, msg.c_str());
}

void meshReceiveNamedCallback(const String &from, const String &msg) {
  Log(DEBUG, "Received message from %u, msg: %s\n", from, msg.c_str());
}

void meshChangeConnCallback() { Log(DEBUG, "Changed connections!\n"); }

void sendMeasurementsToBridge() {
  JsonObject sensor_data = serializeMeasurements(latest_average_measures);
  sendAppData(sensor_data, BRIDGE_NAME);
  resetMeasurements();
};

void readSensors() {
  int n = latest_average_measures.number_of_readings + 1;

  // latest_average_measures.temperature += dht.readTemperature() / n;
  // latest_average_measures.humidity += dht.readHumidity() / n;
  latest_average_measures.temperature += 21;
  latest_average_measures.humidity += 23;
  latest_average_measures.luminosity = 105;
  latest_average_measures.hazardous_gas_warning = false;

  latest_average_measures.number_of_readings = n;
};

void sendAppData(JsonObject app_data, String destination) {
  String cudp_packet = cudp.packageData(app_data);
  mesh.sendSingle(destination, cudp_packet);
}

JsonObject serializeMeasurements(Measurements meas) {
  StaticJsonDocument<256> app_doc;
  JsonObject app_data = app_doc.createNestedObject("data");
  app_data["temperature"] = meas.temperature;
  app_data["humidity"] = meas.humidity;
  app_data["luminosity"] = meas.luminosity;
  app_data["hazardous_gas_warning"] = meas.hazardous_gas_warning;
  app_doc["msg_type"] = MEASUREMENTS;
  return app_doc.as<JsonObject>();
}

void resetMeasurements() {
  latest_average_measures.temperature = 0;
  latest_average_measures.humidity = 0;
  latest_average_measures.luminosity = 0;
  latest_average_measures.hazardous_gas_warning = false;
  latest_average_measures.number_of_readings = 0;
}