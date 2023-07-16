#include <Arduino.h>
#include <painlessMesh.h>
#include <PubSubClient.h>
#include <WiFiClient.h>

#define MESH_PREFIX "sedra"

#define MESH_PASSWORD "smith_eletronica_poli"
#define MESH_PORT 5555

#define STATION_SSID "Eric_celular"
#define STATION_PASSWORD "ericog123"

#define HOSTNAME "MQTT_Bridge"

// Prototypes
void receivedCallback(const uint32_t &from, const String &msg);
void mqttCallback(char *topic, byte *payload, unsigned int length);
void checkIpChange();

IPAddress getlocalIP();

IPAddress myIP(0, 0, 0, 0);
const char *mqttBroker = "broker.hivemq.com";

painlessMesh mesh;
WiFiClient wifiClient;
PubSubClient mqttClient(mqttBroker, 1883, mqttCallback, wifiClient);

void setup()
{
  Serial.begin(115200);

  mesh.setDebugMsgTypes(DEBUG | CONNECTION | COMMUNICATION | REMOTE); // set before init() so that you can see startup messages

  // Channel set to 6. Make sure to use the same channel for your mesh and for you other
  // network (STATION_SSID)
  mesh.init(MESH_PREFIX, MESH_PASSWORD, MESH_PORT, WIFI_AP_STA, 6);

  mesh.onReceive(&receivedCallback);

  mesh.stationManual(STATION_SSID, STATION_PASSWORD); // , 0, IPAddress(192, 168, 240, 69));
  mesh.setHostname(HOSTNAME);

  // Bridge node, should (in most cases) be a root node. See [the wiki](https://gitlab.com/painlessMesh/painlessMesh/wikis/Possible-challenges-in-mesh-formation) for some background
  mesh.setRoot(true);
  // This node and all other nodes should ideally know the mesh contains a root, so call this on all nodes
  mesh.setContainsRoot(true);
}

void loop()
{
  mesh.update();
  mqttClient.loop();
  checkIpChange();
}

void receivedCallback(const uint32_t &from, const String &msg)
{
  Serial.printf("bridge: Received from %u msg=%s\n", from, msg.c_str());
  String topic = "internet-of-poultry/bridge";
  mqttClient.publish(topic.c_str(), msg.c_str());
}

void checkIpChange()
{
  if (myIP != getlocalIP())
  {
    myIP = getlocalIP();
    Serial.println("My IP is " + myIP.toString());
    if (mqttClient.connect("internet-of-poultry-painlessMesh"))
    {
      mqttClient.publish("internet-of-poultry/bridge", "Ready!");
    }
  }
}

IPAddress getlocalIP()
{
  return IPAddress(mesh.getStationIP());
}

void mqttCallback(char *topic, uint8_t *payload, unsigned int length)
{
  Serial.printf("MQTT message received");
}
