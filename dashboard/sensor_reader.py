
from typing import Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

class SensorReader:
    _readings_df: pd.DataFrame
    _has_been_updated: bool

    def __init__(self):
        self._readings_df = pd.DataFrame(
            columns=[
                "temperature",
                "humidity",
                "luminosity",
                "hazardous_gas_warning",
                "node_id",
                "timestamp",
            ]
        )
        self._has_been_updated = False

    def save_measurements(self, meas: Dict):
        self._readings_df.append(pd.DataFrame(meas), ignore_index=True)
        self._has_been_updated = True

    def get_figure(self, node_id: int, meas_type: str) -> go.Figure:
        fig = px.line(
            self._readings_df, x="timestamp", y=[], title="Life expectancy in Canada"
        )

    @property
    def has_been_updated(self):
        return self._has_been_updated