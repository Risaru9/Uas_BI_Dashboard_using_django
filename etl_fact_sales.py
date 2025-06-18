from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os

dag_path = os.path.dirname(__file__)

# -----------------------
# EXTRACT
# -----------------------
def extract():
    dag_path = os.path.dirname(__file__)
    csv_path = os.path.join(dag_path, 'transactions_ip.csv')

    df = pd.read_csv(csv_path)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')

    df.to_csv('/tmp/extracted_sales.csv', index=False)

# -----------------------
# TRANSFORM
# -----------------------
def transform():
    file_path = '/tmp/extracted.csv'
    if not os.path.exists(file_path):
        print(f"[transform] File tidak ditemukan: {file_path}")
        return

    df = pd.read_csv(file_path)

    #dim date
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    dim_date = df[['transaction_date']].drop_duplicates().copy()
    dim_date['date_id'] = dim_date['transaction_date'].dt.strftime('%Y%m%d').astype(int)
    dim_date['year'] = dim_date['transaction_date'].dt.year
    dim_date['month'] = dim_date['transaction_date'].dt.month
    dim_date['day'] = dim_date['transaction_date'].dt.day

    # --- dim_customer
    dim_customer = df[['customer_id']].drop_duplicates().copy()

    # --- dim_product
    dim_product = df[['product_id']].drop_duplicates().copy()

    # --- dim_city
    dim_city = df[['city']].drop_duplicates().copy()
    dim_city['city_id'] = dim_city.index + 1

    # --- fact_sales
    fact_sales = df.merge(dim_date, on='transaction_date') \
                   .merge(dim_city, on='city')

    fact_sales = fact_sales[[
        'transaction_id', 'customer_id', 'product_id', 'date_id', 'city_id',
        'total_amount', 'payment_method', 'shipping_method',
        'delivery_time', 'coupon_code', 'sales_factor'
    ]]

    # Simpan ke /tmp
    dim_date.to_csv('/tmp/dim_date.csv', index=False)
    dim_customer.to_csv('/tmp/dim_customer.csv', index=False)
    dim_product.to_csv('/tmp/dim_product.csv', index=False)
    dim_city.to_csv('/tmp/dim_city.csv', index=False)
    fact_sales.to_csv('/tmp/fact_sales.csv', index=False)

# -----------------------
# LOAD
# -----------------------
def load():
    pd.read_csv('/tmp/dim_date.csv').to_csv(os.path.join(dag_path, 'dim_date.csv'), index=False)
    pd.read_csv('/tmp/dim_customer.csv').to_csv(os.path.join(dag_path, 'dim_customer.csv'), index=False)
    pd.read_csv('/tmp/dim_product.csv').to_csv(os.path.join(dag_path, 'dim_product.csv'), index=False)
    pd.read_csv('/tmp/dim_city.csv').to_csv(os.path.join(dag_path, 'dim_city.csv'), index=False)
    pd.read_csv('/tmp/fact_sales.csv').to_csv(os.path.join(dag_path, 'fact_sales.csv'), index=False)

# -----------------------
# DAG DEFINITION
# -----------------------
with DAG(
    dag_id='etl_fact_sales',
    start_date=datetime(2025, 6, 1),
    schedule='@daily',
    catchup=False,
    tags=['sales', 'fact_sales', 'etl']
) as dag:

    t1 = PythonOperator(
        task_id='extract',
        python_callable=extract
    )

    t2 = PythonOperator(
        task_id='transform',
        python_callable=transform
    )

    t3 = PythonOperator(
        task_id='load',
        python_callable=load
    )

    t1 >> t2 >> t3