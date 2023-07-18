#include <Arduino.h>
#include <painlessMesh.h>
#include "configs.h"
#include "namedMesh.h"

Scheduler scheduler;
namedMesh mesh;
String node_name = NODE_NAME;

Task taskSendMessage(TASK_SECOND * 10, TASK_FOREVER, []() {
  String msg = String("This is a message from ") + NODE_NAME;
  mesh.sendBroadcast(msg);
});

void setup() {
  // ---- Serial configs ----
  Serial.begin(BAUD_RATE);

  // ---- Mesh configs ----
  mesh.setDebugMsgTypes(ERROR | DEBUG | CONNECTION | COMMUNICATION | REMOTE);
  mesh.init(MESH_NAME, MESH_PASSWORD, &scheduler, MESH_PORT, WIFI_AP_STA, MESH_CHANNEL);
  mesh.setName(node_name);

  // ---- Tasks configs ----
  scheduler.addTask(taskSendMessage);
  taskSendMessage.enable();

  // ---- Mesh functions ----
  mesh.onReceive([](uint32_t from, String &msg) {
    Serial.printf("Received message by id from: %u, %s\n", from, msg.c_str());
  });

  mesh.onReceive([](String &from, String &msg) {
    Serial.printf("Received message by name from: %s, %s\n", from.c_str(), msg.c_str());
  });

  mesh.onChangedConnections([]() { Serial.printf("Changed connection\n"); });
}

void loop() { mesh.update(); }
