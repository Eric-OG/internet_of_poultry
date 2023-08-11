from typing import List, Tuple

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
    _temp_df: pd.DataFrame
    _hum_df: pd.DataFrame
    _lum_df: pd.DataFrame
    _haz_gas_df: pd.DataFrame
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

    def read_database(self):
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
        print("Read database!")

    def get_figure(self, node_ids: List[int], meas: str) -> Tuple[go.Figure]:
        filtered_df = self._readings_df[
            self._readings_df["node id"].isin(node_ids)
        ].sort_values(by="timestamp")

        figure = px.line(filtered_df, x="timestamp", y=meas, color="node name", markers=True)
        figure.update_layout(margin=dict(l=20, r=20, t=20, b=20), uirevision=True)
        return figure
