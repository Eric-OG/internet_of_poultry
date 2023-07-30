from typing import List, Dict
import plotly.express as px
from dash import dcc, html, Dash, callback, Input, Output, State
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc

import consts
from mesh_graph import MeshGraph
from mqtt_logger import MqttLogger
from mesh_controller import MeshController
from sensor_reader import SensorReader
from mqtt_client import MqttClient
from styles import stylesheet


mesh_graph = MeshGraph()
mesh_control = MeshController()
mqtt_logger = MqttLogger()
sensors = SensorReader()
client = MqttClient(logger=mqtt_logger, controller=mesh_control, graph=mesh_graph)

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)

node_checklist = dbc.Checklist(id="node-selector", options=[], value=[], inline=True)

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.Div(
                        [
                            cyto.Cytoscape(
                                id="mesh-topology-graph",
                                elements=[],
                                className="w-100",
                            ),
                            dbc.Button(
                                html.I(className="fa-solid fa-lg fa-arrows-rotate"),
                                id="topology-btn",
                                className="p-3",
                                style={"width": "fit-content"},
                            ),
                        ],
                        className="border d-flex flex-column align-items-end",
                    ),
                    dbc.Badge(
                        consts.ConnStatuses.DISCONNECTED,
                        id="conn-status-badge",
                        color="danger",
                        className="w-100 p-2 mt-2 mb-3",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.P(
                                        "SSID da rede conectada: ",
                                        id="conn-name-txt",
                                        className="mb-0 fs-5",
                                    ),
                                    dbc.Badge(
                                        id="conn-name",
                                        color="light",
                                        text_color="primary",
                                        className="mx-2 fs-6",
                                    ),
                                ],
                                className="d-flex align-items-center",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Nome da mesh: ",
                                        id="mesh-name-txt",
                                        className="mb-0 fs-5",
                                    ),
                                    dbc.Badge(
                                        id="mesh-name",
                                        color="light",
                                        text_color="primary",
                                        className="mx-2 fs-6",
                                    ),
                                ],
                                className="d-flex align-items-center",
                            ),
                        ],
                        className="d-flex justify-content-around",
                    ),
                ],
                width=8,
            ),
            justify="center",
            align="center",
            className="pt-4 pb-2",
        ),
        dbc.Row(
            dbc.Col(
                [
                    node_checklist,
                    dcc.Graph(id="temp-readings", figure=px.line()),
                    dcc.Graph(id="hum-readings", figure=px.line()),
                    dcc.Graph(id="lum-readings", figure=px.line()),
                    dcc.Graph(id="gas-readings", figure=px.line()),
                ]
            ),
            style={"paddingBottom": "20%"},
        ),
        dbc.Row(
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H3("Logs de mensagens", className="py-2 px-3"),
                            dbc.Button(
                                "Mostrar logs", id="log-btn", style={"width": "10%"}
                            ),
                        ],
                        className="d-flex justify-content-between",
                        style={"background-color": "rgba(87, 87, 87, 0.2)"},
                    ),
                    html.Div(
                        id="logs-stack",
                        style={"overflowY": "auto", "flex-grow": 1},
                        hidden=True,
                    ),
                ],
                width=12,
                className="mx-0 px-0 d-flex flex-column",
                style={
                    "position": "fixed",
                    "bottom": 0,
                    "background-color": "rgba(87, 87, 87, 0.3)",
                },
                id="logs-container",
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
        if node_label and not el_data.get("root"):
            new_options.append({"label": node_label, "value": el_data.get("id")})
    return new_options


@callback(
    Output("temp-readings", "figure"),
    Output("hum-readings", "figure"),
    Output("lum-readings", "figure"),
    Output("gas-readings", "figure"),
    Input("node-selector", "value"),
    Input("interval-component", "n_intervals"),
)
def update_graph(node_id_list, n_intervals):
    if not (n_intervals and (n_intervals % 60)):
        sensors.read_database()

    node_id_list = [int(node_id) for node_id in node_id_list]
    figures = sensors.get_figures(node_id_list)
    return figures


@callback(
    Output("mesh-topology-graph", "elements"),
    Output("mesh-topology-graph", "layout"),
    Output("mesh-topology-graph", "stylesheet"),
    State("mesh-topology-graph", "elements"),
    State("mesh-topology-graph", "layout"),
    Input("interval-component", "n_intervals"),
)
def update_cytoscape(elements, layout, n_intervals):
    if mesh_graph.has_been_updated or not n_intervals:
        elements, cytoscape_root = mesh_graph.get_cytospace_params()
        layout = {"name": "circle", "animate": True, "roots": cytoscape_root}
    return elements, layout, stylesheet["cytoscape_params"]


@callback(
    Output("logs-stack", "children"),
    State("logs-stack", "children"),
    Input("interval-component", "n_intervals"),
)
def update_logger(children, n_intervals):
    children = mqtt_logger.get_logs() if n_intervals else None
    return children


@callback(Output("hidden-output-dump", "hidden"), Input("topology-btn", "n_clicks"))
def force_topology_update(n_clicks):
    n_clicks and client.publish(consts.TOPOLOGY_REQUEST_TOPIC)
    return True


@callback(
    Output("logs-stack", "hidden"),
    Output("logs-container", "style"),
    Output("log-btn", "children"),
    State("logs-container", "style"),
    Input("log-btn", "n_clicks"),
)
def toggle_logs_display(style, n_clicks):
    if not (n_clicks and n_clicks % 2):
        hidden = True
        style.get("height") and style.pop("height")
        text = "Mostrar logs"
    else:
        hidden = False
        style["height"] = "35%"
        text = "Esconder logs"
    return hidden, style, text


@callback(
    Output("mesh-name", "children"),
    Output("conn-name", "children"),
    Output("conn-status-badge", "children"),
    Output("conn-status-badge", "color"),
    Input("interval-component", "n_intervals"),
)
def update_mesh_params(n_intervals):
    mesh_control.check_conn and client.publish(consts.CHECK_CONN_TOPIC)
    mesh_name, network_name, conn_status = mesh_control.get_status()
    color_str = "success" if conn_status == consts.ConnStatuses.CONNECTED else "danger"
    return mesh_name, network_name, conn_status, color_str


if __name__ == "__main__":
    client.connect()
    app.run(debug=True)
