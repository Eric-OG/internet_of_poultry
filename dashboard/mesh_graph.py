
from typing import Dict, List
from networkx import Graph

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
        is_root = bool(node.get("root"))
        neighbor_nodes = node.get("subs")

        node_id_padded = node_id.zfill(10)
        node_name = self._name_map.get(node_id)
        label = node_name if node_name else node_id_padded

        self._mesh_graph.add_node(node_id, label=label, is_root=is_root)

        if neighbor_nodes:
            self._mesh_graph.add_edges_from(
                [
                    (node_id, str(neighbor["nodeId"]))
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
                'grabbable': False
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
        return self._cytoscape_elements, self._cytoscape_root

    @property
    def has_been_updated(self):
        return self._has_been_updated
    
    @has_been_updated.setter
    def has_been_updated(self, state):
        self._has_been_updated = state