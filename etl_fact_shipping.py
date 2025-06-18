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

    df.to_csv('/tmp/extracted_shipping.csv', index=False)

# -----------------------
# TRANSFORM
# -----------------------
def transform():
    file_path = '/tmp/extracted_shipping.csv'
    if not os.path.exists(file_path):
        print(f"[transform] File tidak ditemukan: {file_path}")
        return

    df = pd.read_csv(file_path)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')

    # --- dim_date
    dim_date = df[['transaction_date']].drop_duplicates().copy()
    dim_date['date_id'] = dim_date['transaction_date'].dt.strftime('%Y%m%d').astype(int)
    dim_date['year'] = dim_date['transaction_date'].dt.year
    dim_date['month'] = dim_date['transaction_date'].dt.month
    dim_date['day'] = dim_date['transaction_date'].dt.day

    # --- dim_city
    dim_city = df[['city']].drop_duplicates().copy()
    dim_city['city_id'] = dim_city.index + 1

    # --- dim_shipping_method
    dim_shipping_method = df[['shipping_method']].drop_duplicates().copy()
    dim_shipping_method['shipping_method_id'] = dim_shipping_method.index + 1

    # --- dim_delivery_category
    def categorize_delivery_time(val):
        val = str(val).lower()
        if '1' in val:
            return 'Cepat'
        elif '2-3' in val or '2' in val or '3' in val:
            return 'Sedang'
        elif '4' in val or '5' in val or 'minggu' in val:
            return 'Lambat'
        return 'Tidak Diketahui'

    df['delivery_category'] = df['delivery_time'].fillna('Tidak Diketahui').apply(categorize_delivery_time)
    dim_delivery_category = df[['delivery_category']].drop_duplicates().copy()
    dim_delivery_category['delivery_category_id'] = dim_delivery_category.index + 1

    # --- fact_shipping
    fact_shipping = df.merge(dim_date, on='transaction_date') \
                      .merge(dim_city, on='city') \
                      .merge(dim_shipping_method, on='shipping_method') \
                      .merge(dim_delivery_category, on='delivery_category')

    fact_shipping = fact_shipping[[
        'transaction_id', 'date_id', 'city_id',
        'shipping_method_id', 'delivery_category_id'
    ]]

    # Simpan hasil transformasi
    dim_date.to_csv('/tmp/dim_date_shipping.csv', index=False)
    dim_city.to_csv('/tmp/dim_city_shipping.csv', index=False)
    dim_shipping_method.to_csv('/tmp/dim_shipping_method.csv', index=False)
    dim_delivery_category.to_csv('/tmp/dim_delivery_category.csv', index=False)
    fact_shipping.to_csv('/tmp/fact_shipping.csv', index=False)

# -----------------------
# LOAD
# -----------------------
def load():
    pd.read_csv('/tmp/dim_date_shipping.csv').to_csv(os.path.join(dag_path, 'dim_date_shipping.csv'), index=False)
    pd.read_csv('/tmp/dim_city_shipping.csv').to_csv(os.path.join(dag_path, 'dim_city_shipping.csv'), index=False)
    pd.read_csv('/tmp/dim_shipping_method.csv').to_csv(os.path.join(dag_path, 'dim_shipping_method.csv'), index=False)
    pd.read_csv('/tmp/dim_delivery_category.csv').to_csv(os.path.join(dag_path, 'dim_delivery_category.csv'), index=False)
    pd.read_csv('/tmp/fact_shipping.csv').to_csv(os.path.join(dag_path, 'fact_shipping.csv'), index=False)

# -----------------------
# DAG DEFINITION
# -----------------------
with DAG(
    dag_id='etl_fact_shipping',
    start_date=datetime(2025, 6, 1),
    schedule='@daily',
    catchup=False,
    tags=['shipping', 'fact_shipping', 'etl']
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
