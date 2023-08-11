from typing import Dict
from datetime import datetime
from dateutil import tz
from json import loads

from boto3.session import Session
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import psycopg

logger = Logger()


def get_credentials() -> Dict:
    secret_name = "lambda_iot_credentials"
    region_name = "sa-east-1"

    session = Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    secret = get_secret_value_response["SecretString"]
    return loads(secret)


def lambda_handler(event: Dict, context: LambdaContext):
    db_credentials = get_credentials()

    conn = psycopg.connect(
        host=db_credentials["host"],
        port=db_credentials["port"],
        user=db_credentials["username"],
        password=db_credentials["password"],
        dbname=db_credentials["dbname"],
        sslmode="require",
    )
    logger.info("Connected! Event is: " + str(event))

    node_id = event["node_id"]
    node_name = event["node_name"] if event["node_name"] else None
    temperature = event["temperature"]
    humidity = event["humidity"]
    luminosity = event["luminosity"]
    hazardous_gas_warning = event["hazardous_gas_warning"]
    timestamp = datetime.now(tz=tz.gettz("America/Sao_Paulo")).replace(tzinfo=None)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO measurements
                (node_id, node_name, temperature, humidity, luminosity, hazardous_gas_warning, timestamp)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                node_id,
                node_name,
                temperature,
                humidity,
                luminosity,
                hazardous_gas_warning,
                timestamp,
            ),
        )

    conn.commit()


if __name__ == "__main__":
    event_example = {
        "node_id": 123456789,
        "node_name": "patterson",
        "temperature": 23.2,
        "humidity": 61,
        "luminosity": 0.7,
        "hazardous_gas_warning": 0.1,
    }
    lambda_handler(event_example, None)
