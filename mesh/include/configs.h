#ifndef MESH_NAME
#define MESH_NAME "iop_mesh_default"
#endif

#ifndef MESH_PASSWORD
#define MESH_PASSWORD "default_password"
#endif

#ifndef MESH_PORT
#define MESH_PORT 5555
#endif

#ifndef MESH_CHANNEL
#define MESH_CHANNEL 1
#endif

#ifndef AP_SSID
#define AP_SSID "default_wifi"
#endif

#ifndef AP_PASSWORD
#define AP_PASSWORD "default_wifi_password"
#endif

#ifndef MQTT_BROKER
#define MQTT_BROKER "broker.hivemq.com"
#endif

#ifndef MQTT_PORT
#define MQTT_PORT 1883
#endif

#ifndef DEBUG_TOPIC
#define DEBUG_TOPIC "internet-of-poultry/debug"
#endif

#ifndef DASH_ROOT_TOPIC
#define DASH_ROOT_TOPIC "internet-of-poultry/dash/#"
#endif

#ifndef CONN_CHECK_TOPIC
#define CONN_CHECK_TOPIC "internet-of-poultry/dash/hello"
#endif

#ifndef CONN_ACK_TOPIC
#define CONN_ACK_TOPIC "internet-of-poultry/mesh/hello"
#endif

#ifndef TOPOLOGY_REQUEST
#define TOPOLOGY_REQUEST "internet-of-poultry/dash/topology-request"
#endif

#ifndef TOPOLOGY_RESPONSE
#define TOPOLOGY_RESPONSE "internet-of-poultry/mesh/topology-response"
#endif

#ifndef MEASUREMENTS_TOPIC
#define MEASUREMENTS_TOPIC "internet-of-poultry/mesh/measurements"
#endif

#ifndef BAUD_RATE
#define BAUD_RATE 115200
#endif

#ifndef NODE_NAME
#define NODE_NAME "default_node_name"
#endif

#ifndef BRIDGE_NAME
#define BRIDGE_NAME "default_bridge_name"
#endif

#ifndef MQTT_DEBUG
#define MQTT_DEBUG 0
#endif

#ifndef DHT_PIN
#define DHT_PIN 7
#endif

#ifndef DHT_TYPE
#define DHT_TYPE DHT11
#endif

#ifndef NTP_SERVER
#define NTP_SERVER "south-america.pool.ntp.org"
#endif

#ifndef GMT_OFFSET_SECS
#define GMT_OFFSET_SECS 10800
#endif

#ifndef DST_OFFSET_SECS
#define DST_OFFSET_SECS 0
#endif