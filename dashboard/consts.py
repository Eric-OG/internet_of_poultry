from enum import StrEnum

ROOT_TOPIC = 'internet-of-poultry/#'
CHECK_CONN_TOPIC = 'internet-of-poultry/dash/hello'
ACK_CONN_TOPIC = 'internet-of-poultry/mesh/hello'
TOPOLOGY_REQUEST_TOPIC = 'internet-of-poultry/dash/topology-request'
TOPOLOGY_RESPONSE_TOPIC = 'internet-of-poultry/mesh/topology-response'
MEASUREMENTS_TOPIC = '"internet-of-poultry/mesh/measurements"'

class ConnStatuses(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"