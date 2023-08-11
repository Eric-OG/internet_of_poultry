import json
from functools import partial
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

from mqtt_logger import MqttLogger
from mesh_controller import MeshController
from mesh_graph import MeshGraph
import consts


class MqttClient:
    CLIENT_ID = "iop-dash"
    ENDPOINT = "a108z6ol7a611d-ats.iot.sa-east-1.amazonaws.com"
    # Create credentials (or get) if necessary
    PATH_TO_CERTIFICATE = "certificates/dash-certificate.pem.crt"
    PATH_TO_PRIVATE_KEY = "certificates/dash-private.pem.key"
    PATH_TO_AMAZON_ROOT_CA_1 = "certificates/rootCA1.pem"

    _conn: mqtt.Connection
    _logger: MqttLogger
    _controller: MeshController
    _graph: MeshGraph

    def __init__(
        self,
        logger: MqttLogger,
        controller: MeshController,
        graph: MeshGraph,
    ):
        self._logger = logger
        self._controller = controller
        self._graph = graph

    def connect(self):
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        self._conn = mqtt_connection_builder.mtls_from_path(
            endpoint=self.ENDPOINT,
            cert_filepath=self.PATH_TO_CERTIFICATE,
            pri_key_filepath=self.PATH_TO_PRIVATE_KEY,
            client_bootstrap=client_bootstrap,
            ca_filepath=self.PATH_TO_AMAZON_ROOT_CA_1,
            client_id=self.CLIENT_ID,
            clean_session=False,
            keep_alive_secs=6,
        )
        print(f"Connecting to {self.ENDPOINT} with client ID '{self.CLIENT_ID}'...")
        # Make the connect() call
        connect_future = self._conn.connect()
        # Future.result() waits until a result is available
        connect_future.result()
        print("Connected to MQTT!")

        subscribe_future, _ = self._conn.subscribe(
            consts.ROOT_TOPIC,
            qos=mqtt.QoS.AT_MOST_ONCE,
            callback=partial(
                self._on_receive,
                self._logger,
                self._controller,
                self._graph,
            ),
        )

        subscribe_future.result()
        print(f"Subscribed to {consts.ROOT_TOPIC}")

    def publish(self, topic: str, message: str = None):
        payload = json.dumps(message) if message else ""
        publish_future, _ = self._conn.publish(
            topic=topic, payload=payload, qos=mqtt.QoS.AT_MOST_ONCE
        )
        publish_future.result()

    @staticmethod
    def _on_receive(
        logger: MqttLogger,
        controller: MeshController,
        graph: MeshGraph,
        topic: str,
        payload: bytes,
        dup: bool,
        qos: mqtt.QoS,
        retain: bool,
        **kwargs,
    ):
        json_payload = json.loads(payload.decode("utf-8")) if payload else None
        logger.log_message(msg=json_payload, topic=topic)

        match topic:
            case consts.ACK_CONN_TOPIC:
                controller.refresh_connection_status()
                mesh_name = json_payload["mesh_name"]
                mesh_network = json_payload["mesh_network"]
                controller.update_mesh_status(mesh_name=mesh_name, network_name=mesh_network)

            case consts.TOPOLOGY_RESPONSE_TOPIC:
                controller.refresh_connection_status()
                mesh_tree_root = json_payload["mesh_tree"]
                name_map = json_payload["name_map"]
                graph.update_graph(mesh_tree_root=mesh_tree_root, name_map=name_map)
