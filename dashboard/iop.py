from typing import List, Dict
import json
import paho.mqtt.client as mqtt
import plotly.express as px
from dash import Dash, html, Input, Output, callback, dcc, State
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc

import consts
from mesh_graph import MeshGraph
from mqtt_logger import MqttLogger
from sensor_reader import SensorReader
from styles import stylesheet


def _on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("internet-of-poultry/#")


def _on_message(client, userdata, msg):
    json_payload = json.loads(msg.payload.decode("utf-8")) if msg.payload else None
    logger.log_message(msg=json_payload, topic=msg.topic)

    print(msg.topic)

    match msg.topic:
        case consts.TOPOLOGY_RESPONSE_TOPIC:
            print(json_payload)
            mesh_tree_root = json_payload["mesh_tree"]
            name_map = json_payload["name_map"]
            mesh_graph.update_graph(mesh_tree_root=mesh_tree_root, name_map=name_map)
        case "internet-of-poultry/measurements":
            sensors.save_measurements(json_payload)


mesh_graph = MeshGraph()
logger = MqttLogger()
sensors = SensorReader()
client = mqtt.Client()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

node_checklist = dbc.Checklist(id="node-selector", options=[], value=[], inline=True)

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1("Internet of Poultry"),
                    html.Hr(),
                    node_checklist,
                    dbc.Row(
                        dbc.Col(
                            [
                                cyto.Cytoscape(
                                    id="mesh-topology-graph",
                                    elements=[],
                                    className="w-50 border",
                                ),
                                dbc.Button(
                                    "Atualizar topologia da mesh",
                                    id="topology-btn",
                                    className="me-2",
                                ),
                            ]
                        ),
                        justify="start",
                        align="center",
                        className="px-3",
                    ),
                    dcc.Graph(id="temp-readings", figure=px.line()),
                    dcc.Graph(id="hum-readings", figure=px.line()),
                    dcc.Graph(id="lum-readings", figure=px.line()),
                ],
                style={"paddingBottom": "20%"},
            ),
            className="p-2",
        ),
        dbc.Row(
            dbc.Col(
                [
                    html.H3("Logs de mensagens", className="py-2 px-3"),
                    html.Div(
                        id="logs-stack", style={"overflowY": "auto", 'flex-grow': 1}
                    ),
                ],
                className="mx-0 px-0",
                style={
                    "position": "fixed",
                    "bottom": 0,
                    "height": "35%",
                    "width": "100%",
                    "display": "flex",
                    "flex-direction": "column",
                    "background-color": "rgba(87, 87, 87, 0.25)"
                },
            ),
        ),
        dcc.Interval(id="interval-component", interval=1000, n_intervals=0),
        html.P(id="hidden-output-dump", hidden=True),
    ],
    fluid=True,
    style={"height": "100vh"},
)


@callback(
    Output("node-selector", "options"),
    Input("mesh-topology-graph", "elements"),
)
def update_node_checklist(elements: List[Dict]):
    new_options = []

    for el in elements:
        el_data = el.get("data", {})
        node_label = el_data.get("label")
        if node_label:
            new_options.append({"label": node_label, "value": el_data.get("id")})
    return new_options


# @callback(
#     Output("sensor-readings", "figure"),
#     State("sensor-readings", "figure"),
#     Input("interval-component", "n_intervals"),
# )
# def update_graph(figure, n_intervals):
#     if sensors.has_been_updated:
#         figure = sensors.get_figure()
#     return figure


@callback(
    Output("mesh-topology-graph", "elements"),
    Output("mesh-topology-graph", "layout"),
    Output("mesh-topology-graph", "stylesheet"),
    State("mesh-topology-graph", "elements"),
    State("mesh-topology-graph", "layout"),
    Input("interval-component", "n_intervals"),
)
def update_cytoscape(elements, layout, n_intervals):
    if mesh_graph.has_been_updated:
        elements, cytoscape_root = mesh_graph.get_cytospace_params()
        layout = {"name": "breadthfirst", "animate": True, "roots": cytoscape_root}
    return elements, layout, stylesheet["cytoscape_params"]


@callback(Output("hidden-output-dump", "hidden"), Input("topology-btn", "n_clicks"))
def force_topology_update(n_clicks):
    n_clicks and client.publish(consts.TOPOLOGY_REQUEST_TOPIC)
    return True


@callback(
    Output("logs-stack", "children"),
    State("logs-stack", "children"),
    Input("interval-component", "n_intervals"),
)
def update_logger(children, n_intervals):
    if logger.has_been_updated:
        children = logger.get_logs()
    return children


if __name__ == "__main__":
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect("broker.hivemq.com", 1883)
    client.loop_start()

    app.run(debug=True)
