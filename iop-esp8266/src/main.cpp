//************************************************************
// this is a simple example that uses the painlessMesh library
//
// This example shows how to build a mesh with named nodes
//
//************************************************************
#include "namedMesh.h"

#define MESH_SSID "sedra"
#define MESH_PASSWORD "smith_eletronica_poli"
#define MESH_PORT 5555

Scheduler userScheduler; // to control your personal task
namedMesh mesh;

String nodeSender = "patterson";
String nodeReceiver = "hennessy";

Task taskSendMessage(TASK_SECOND * 30, TASK_FOREVER, []()
                     {
    String msg = String("This is a message from: ") + nodeSender;
    mesh.sendBroadcast(msg); }); // start with a one second interval

void setup()
{
  Serial.begin(115200);

  mesh.setDebugMsgTypes(ERROR | DEBUG | CONNECTION); // set before init() so that you can see startup messages

  mesh.init(MESH_SSID, MESH_PASSWORD, &userScheduler, MESH_PORT, WIFI_AP_STA, 6);

  mesh.setName(nodeSender); // This needs to be an unique name!

  mesh.onReceive([](uint32_t from, String &msg)
                 { Serial.printf("Received message by id from: %u, %s\n", from, msg.c_str()); });

  mesh.onReceive([](String &from, String &msg)
                 { Serial.printf("Received message by name from: %s, %s\n", from.c_str(), msg.c_str()); });

  mesh.onChangedConnections([]()
                            { Serial.printf("Changed connection\n"); });

  userScheduler.addTask(taskSendMessage);
  taskSendMessage.enable();
}

void loop()
{
  // it will run the user scheduler as well
  mesh.update();
}
