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


def line_graph(title: str, graph_id: str, dropdown_id: str):
    return html.Div(
        [
            html.H1(title),
            html.Div(
                [
                    dcc.Dropdown(
                        id=dropdown_id,
                        options=[],
                        value=[],
                        multi=True,
                        style={"width": "100%", "font-size": 20},
                    ),
                ],
                className="mt-3",
                style={"width": "60%"},
            ),
            dcc.Graph(
                id=graph_id,
                figure=px.line(),
                className="w-100 mb-5",
                style={"height": "55vh"},
            ),
        ],
        className="w-100 mb-5 d-flex flex-column align-items-center",
    )


mesh_graph = MeshGraph()
mesh_control = MeshController()
mqtt_logger = MqttLogger()
sensors = SensorReader()
client = MqttClient(logger=mqtt_logger, controller=mesh_control, graph=mesh_graph)

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)


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
            className="pt-5 pb-2",
        ),
        dbc.Row(
            dbc.Col(
                html.Hr(),
                width=11,
            ),
            justify="center",
            align="center",
            className="pt-4 pb-5",
        ),
        dbc.Row(
            dbc.Col(
                [
                    line_graph("Temperatura", "temp-readings", "selector-temp"),
                    line_graph("Umidade", "hum-readings", "selector-hum"),
                    line_graph("Luminosidade", "lum-readings", "selector-lum"),
                    line_graph(
                        "Concentração de gases tóxicos",
                        "gas-readings",
                        "selector-gas",
                    ),
                ],
                width=10,
            ),
            justify="center",
            align="center",
            style={"padding-bottom": "20%"},
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
                        style={"background-color": "rgba(187, 187, 187, 0.8)"},
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
                    "background-color": "rgba(155, 155, 155, 0.9)",
                },
                id="logs-container",
            ),
        ),
        dcc.Interval(id="interval-component", interval=3000, n_intervals=0),
        html.P(id="hidden-output-dump", hidden=True),
    ],
    fluid=True,
    style={"height": "100vh"},
)


@callback(
    Output("selector-temp", "options"),
    Output("selector-temp", "value"),
    Output("selector-hum", "options"),
    Output("selector-hum", "value"),
    Output("selector-lum", "options"),
    Output("selector-lum", "value"),
    Output("selector-gas", "options"),
    Output("selector-gas", "value"),
    State("selector-temp", "value"),
    State("selector-hum", "value"),
    State("selector-lum", "value"),
    State("selector-gas", "value"),
    Input("mesh-topology-graph", "elements"),
)
def update_node_checklist(
    temp_values: List[int],
    hum_values: List[int],
    lum_values: List[int],
    gas_values: List[int],
    elements: List[Dict],
):
    new_options = []
    new_values = []

    for el in elements:
        el_data = el.get("data", {})
        node_label = el_data.get("label")
        el_id = el_data.get("id")
        if node_label and not el_data.get("root"):
            new_options.append({"label": node_label, "value": el_id})
            new_values.append(el_id)

    if mesh_graph.has_been_updated:
        mesh_graph.has_been_updated = False
        return tuple([new_options, new_values] * 4)

    return [
        new_options,
        temp_values,
        new_options,
        hum_values,
        new_options,
        lum_values,
        new_options,
        gas_values,
    ]


@callback(
    Output("temp-readings", "figure"),
    Input("selector-temp", "value"),
    Input("interval-component", "n_intervals"),
)
def update_temp_graph(node_id_list, n_intervals):
    node_id_list = [int(node_id) for node_id in node_id_list]
    return sensors.get_figure(node_id_list, "temperature")


@callback(
    Output("hum-readings", "figure"),
    Input("selector-hum", "value"),
    Input("interval-component", "n_intervals"),
)
def update_hum_graph(node_id_list, n_intervals):
    node_id_list = [int(node_id) for node_id in node_id_list]
    return sensors.get_figure(node_id_list, "humidity")


@callback(
    Output("lum-readings", "figure"),
    Input("selector-lum", "value"),
    Input("interval-component", "n_intervals"),
)
def update_lum_graph(node_id_list, n_intervals):
    node_id_list = [int(node_id) for node_id in node_id_list]
    return sensors.get_figure(node_id_list, "luminosity")


@callback(
    Output("gas-readings", "figure"),
    Input("selector-gas", "value"),
    Input("interval-component", "n_intervals"),
)
def update_gas_graph(node_id_list, n_intervals):
    node_id_list = [int(node_id) for node_id in node_id_list]
    return sensors.get_figure(node_id_list, "hazardous gas warning")


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
    Output("hidden-output-dump", "children"), Input("interval-component", "n_intervals")
)
def update_measurements(n_intervals):
    if not (n_intervals and (n_intervals % 20)):
        sensors.read_database()


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
