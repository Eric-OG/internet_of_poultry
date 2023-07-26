from datetime import datetime
import psycopg


def get_password():
    return

def lambda_handler(event, context):
    db_password = get_password()

    conn = psycopg.connect(
        host="internet-of-poultry.c0v17euafbbn.sa-east-1.rds.amazonaws.com",
        port=5432,
        user='lambda_iot',
        password=db_password,
        dbname='iop'
    )

    print("Conectado!")

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO measurements
                (node_id, node_name, temperature, humidity, luminosity, hazardous_gas_warning, timestamp)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s);
            """,
            (11, "hennessy", 19.1, 0.8, 0.9, False, datetime.now())
        )
    
    print("Valores inseridos:")

    conn.commit()