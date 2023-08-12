from typing import List, Dict

from dotenv import dotenv_values
import pandas as pd
import psycopg
import plotly.express as px
import plotly.graph_objs as go


class SensorReader:
    _conn: psycopg.Connection
    _latest_id_read: int
    _has_been_updated: bool

    _readings_df: pd.DataFrame
    _df_cols_names = [
        "id",
        "node id",
        "node name",
        "temperature",
        "humidity",
        "luminosity",
        "hazardous gas warning",
        "timestamp",
    ]
    _measurements = [
        "temperature",
        "humidity",
        "luminosity",
        "hazardous gas warning",
    ]

    def __init__(self):
        db_credentials = dotenv_values("credentials.env")
        self._conn = psycopg.connect(
            host=db_credentials["DB_HOST"],
            port=db_credentials["DB_PORT"],
            user=db_credentials["DB_USER"],
            password=db_credentials["DB_PASSWORD"],
            dbname=db_credentials["DB_NAME"],
            sslmode="require",
        )
        print("Connected to database!")

        self._readings_df = pd.DataFrame(columns=self._df_cols_names)
        self._latest_id_read = 0
        self.update_measurements()

    def update_measurements(self):
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM measurements WHERE id > %s", (self._latest_id_read,)
            )
            records = cur.fetchall()
        self._conn.commit()

        new_records_df = pd.DataFrame(records, columns=self._df_cols_names)
        self._readings_df = pd.concat(
            [self._readings_df, new_records_df], ignore_index=True
        )
        self._latest_id_read = records[-1][0] if records else self._latest_id_read
        print("Read database measurements!")

    def get_figure(self, node_ids: List[int], meas: str) -> go.Figure:
        filtered_df = self._readings_df[
            self._readings_df["node id"].isin(node_ids)
        ].sort_values(by="timestamp")

        # Scale adjustment: better to fix in mesh
        if meas == "hazardous gas warning":
            filtered_df[meas] = 1 - filtered_df[meas]

        figure = px.line(
            filtered_df, x="timestamp", y=meas, color="node name", markers=True
        )
        figure.update_layout(margin=dict(l=20, r=20, t=20, b=20), uirevision=True)
        return figure

    def get_nodes(self) -> List[Dict]:
        nodes = self._readings_df[["node name", "node id"]].drop_duplicates(
            subset=["node name"]
        )
        return nodes.to_dict(orient="records")

    def get_node_ids(self) -> List[int]:
        return self._readings_df["node id"].unique()
