#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <painlessMesh.h>
#include "ChickenUDP.h"
#include "configs.h"
#include "namedMesh.h"

#define LDR_PIN A0
#define MQ_PIN D4
#define DHT_PIN D5

typedef struct Measurements {
  float temperature;
  float humidity;
  float luminosity;
  float hazardous_gas_warning;
  float number_of_readings;
} Measurements;

// Function prototypes
void meshReceiveCallback(const uint32_t &from, const String &msg);
void meshReceiveNamedCallback(const String &from, const String &msg);
void meshChangeConnCallback();
void resetMeasurements();
void sendAppData(DataJson *app_data, String destination);
void readSensors();
void sendMeasurementsToBridge();
void serializeMeasurements(DataJson *app_data);

// Tasks
Task readSensorsTask(TASK_SECOND * 5, TASK_FOREVER, &readSensors);
Task sendMeasurementsTask(TASK_SECOND * 30, TASK_FOREVER, &sendMeasurementsToBridge);

// Global variables
Scheduler scheduler;
namedMesh mesh;
DHT dht(DHT_PIN, DHT_TYPE);
String node_name = NODE_NAME;
String bridge_name = BRIDGE_NAME;
Measurements latest_average_measures;
ChickenUDP cudp;

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
  DataJson app_data;
  serializeMeasurements(&app_data);
  sendAppData(&app_data, BRIDGE_NAME);
  resetMeasurements();
};

void sendAppData(DataJson *app_data, String destination) {
  String cudp_packet = cudp.packageData(app_data);
  mesh.sendSingle(destination, cudp_packet);
}

void readSensors() {
  latest_average_measures.temperature += dht.readTemperature();
  latest_average_measures.humidity += dht.readHumidity();
  latest_average_measures.luminosity += (float(analogRead(LDR_PIN)) / float(1023));
  latest_average_measures.hazardous_gas_warning += digitalRead(MQ_PIN);
  // Mock
  // latest_average_measures.temperature += 21;
  // latest_average_measures.humidity += 23;
  // latest_average_measures.luminosity += 105;
  // latest_average_measures.hazardous_gas_warning += 0;
  // latest_average_measures.number_of_readings += 1;

  Log(DEBUG, "Sensor data:\n\ttemp:%.1f\n\thum:%.1f\n\tlum:%.1f\n\tgas:%.1f\n",
      latest_average_measures.temperature, latest_average_measures.humidity,
      latest_average_measures.luminosity, latest_average_measures.hazardous_gas_warning);
};

void serializeMeasurements(DataJson *app_data) {
  JsonObject meas_json = (*app_data).createNestedObject("data");
  float num_of_reads = latest_average_measures.number_of_readings;

  meas_json["temperature"] = latest_average_measures.temperature / num_of_reads;
  meas_json["humidity"] = latest_average_measures.humidity / num_of_reads;
  meas_json["luminosity"] = latest_average_measures.luminosity / num_of_reads;
  meas_json["hazardous_gas_warning"] =
      latest_average_measures.hazardous_gas_warning / num_of_reads;

  (*app_data)["msg_type"] = MEASUREMENTS;
}

void resetMeasurements() {
  latest_average_measures.temperature = 0;
  latest_average_measures.humidity = 0;
  latest_average_measures.luminosity = 0;
  latest_average_measures.hazardous_gas_warning = 0;
  latest_average_measures.number_of_readings = 0;
  Log(DEBUG, "Resetting measurements!\n");
}