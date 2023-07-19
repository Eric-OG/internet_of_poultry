from typing import Dict, List
import json

from networkx import Graph
import paho.mqtt.client as mqtt
from dash import Dash, html, Input, Output, callback, dcc, State
import dash_cytoscape as cyto


class MeshGraph:
    _mesh_graph: Graph
    _name_map: Dict
    _cytoscape_elements: List
    _cytoscape_root: str
    _has_been_updated: bool

    def __init__(self):
        self._mesh_graph = Graph()
        self._name_map = None
        self._cytoscape_elements = []
        self._cytoscape_root = ""
        self._has_been_updated = False

    def _recursive_graph_parser(self, node: Dict):
        node_id = str(node["nodeId"])
        label = self._name_map.get(node_id)
        is_root = bool(node.get("root"))
        neighbor_nodes = node.get("subs")
        self._mesh_graph.add_node(node_id.zfill(10), label=label, is_root=is_root)

        if neighbor_nodes:
            self._mesh_graph.add_edges_from(
                [
                    (node_id.zfill(10), str(neighbor["nodeId"]).zfill(10))
                    for neighbor in neighbor_nodes
                ]
            )
            for neighbor in neighbor_nodes:
                self._recursive_graph_parser(node=neighbor)

    def _update_cytoscape(self):
        root_id = [
            node_id
            for node_id, node_data in self._mesh_graph.nodes(data=True)
            if node_data["is_root"]
        ][0]

        cytoscape_nodes = [
            {
                "data": {
                    "id": node_id,
                    "label": node_data["label"],
                    "root": node_data["is_root"],
                },
            }
            for node_id, node_data in self._mesh_graph.nodes(data=True)
        ]

        cytoscape_edges = [
            {"data": {"source": edge[0], "target": edge[1]}}
            for edge in self._mesh_graph.edges()
        ]

        self._cytoscape_elements = cytoscape_nodes + cytoscape_edges
        self._cytoscape_root = '[id = "' + root_id + '"]'

    def update_graph(self, mesh_tree_root: Dict, name_map: Dict):
        self._mesh_graph.clear()
        self._name_map = name_map
        self._recursive_graph_parser(node=mesh_tree_root)
        self._update_cytoscape()
        self._has_been_updated = True

    def get_cytospace_params(self):
        self._has_been_updated = False
        return self._cytoscape_elements, self._cytoscape_root

    @property
    def has_been_updated(self):
        return self._has_been_updated


def _on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("internet-of-poultry/topology_response")


def _on_message(client, userdata, msg):
    mesh_topology = json.loads(msg.payload.decode("utf-8"))
    mesh_tree_root = mesh_topology["node_tree"]
    name_map = mesh_topology["name_map"]
    mesh_graph.update_graph(mesh_tree_root=mesh_tree_root, name_map=name_map)


app = Dash(__name__)


mesh_graph = MeshGraph()


app.layout = html.Div(
    html.Div(
        [
            cyto.Cytoscape(
                id="mesh-topology-graph",
                elements=[],
                layout={"name": "breadthfirst", "animate": True},
                stylesheet=[
                    {"selector": "node", "style": {"content": "data(label)"}},
                    {
                        "selector": "[root > 0]",
                        "style": {"background-color": "red", "content": "data(label)"},
                    },
                ],
                style={"width": "100%", "height": "750px"},
            ),
            dcc.Interval(id="interval-component", interval=5000, n_intervals=0),
        ]
    )
)


@callback(
    Output("mesh-topology-graph", "elements"),
    Output("mesh-topology-graph", "layout"),
    State("mesh-topology-graph", "elements"),
    State("mesh-topology-graph", "layout"),
    Input("interval-component", "n_intervals"),
)
def update_elements(elements, layout, n_intervals):
    if mesh_graph.has_been_updated:
        elements, cytoscape_root = mesh_graph.get_cytospace_params()
        layout["roots"] = cytoscape_root
    return elements, layout


if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect("broker.hivemq.com", 1883)
    client.loop_start()

    app.run(debug=True)
