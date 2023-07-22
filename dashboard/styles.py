stylesheet = {
    "logWrapper": {
        "position": "fixed",
        "bottom": 0,
        "width": "100%",
        "height": 200,
        "backgroundColor": "red",
    },
    "logTerminal": {
        "width": "100%",
        "height": "100%",
        "overflowY": "scroll",
        "backgroundColor": "grey",
        "whiteSpace": "pre-wrap",
    },
    "cytoscape_params": [
        {"selector": "node", "style": {"content": "data(label)"}},
        {
            "selector": "[root > 0]",
            "style": {
                "background-color": "red",
                "content": "data(label)",
            },
        },
    ],
}
