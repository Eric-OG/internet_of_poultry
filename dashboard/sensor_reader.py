from dotenv import dotenv_values
import pandas as pd
import psycopg
import plotly.express as px
import plotly.graph_objs as go


class SensorReader:
    _conn: psycopg.Connection
    _readings_df: pd.DataFrame
    _latest_id_read: int
    _has_been_updated: bool
    _df_cols_names = [
        "id",
        "node_id",
        "node_name",
        "temperature",
        "humidity",
        "luminosity",
        "hazardous_gas_warning",
        "timestamp",
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
        self._has_been_updated = False

    def read_database(self):
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM measurements WHERE id > %s", (self._latest_id_read,)
            )
            records = cur.fetchall()
            new_records_df = pd.DataFrame(records, columns=self._df_cols_names)

            self._readings_df = pd.concat(
                [self._readings_df, new_records_df], ignore_index=True
            )
            self._latest_id_read = records[-1][0] if records else self._latest_id_read
            self._has_been_updated = True
        self._conn.commit()

    def get_figure(self, node_id: int, meas_type: str) -> go.Figure:
        fig = px.line(
            self._readings_df, x="timestamp", y=[], title="Life expectancy in Canada"
        )

    @property
    def has_been_updated(self):
        return self._has_been_updated
