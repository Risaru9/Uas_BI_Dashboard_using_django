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
    df.to_csv('/tmp/extracted_payment.csv', index=False)

# -----------------------
# TRANSFORM
# -----------------------
def transform():
    file_path = '/tmp/extracted_payment.csv'
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

    # --- dim_customer
    dim_customer = df[['customer_id']].drop_duplicates().copy()

    # --- dim_payment_method
    dim_payment_method = df[['payment_method']].drop_duplicates().copy()
    dim_payment_method['payment_method_id'] = dim_payment_method.index + 1

    # --- dim_coupon
    df['coupon_code'] = df['coupon_code'].fillna('NO_COUPON')
    dim_coupon = df[['coupon_code']].drop_duplicates().copy()
    dim_coupon['coupon_id'] = dim_coupon.index + 1

    # --- fact_payment
    fact_payment = df.merge(dim_date, on='transaction_date') \
                     .merge(dim_payment_method, on='payment_method') \
                     .merge(dim_coupon, on='coupon_code')

    fact_payment = fact_payment[[
        'transaction_id', 'customer_id', 'date_id',
        'payment_method_id', 'coupon_id',
        'total_amount', 'sales_factor'
    ]]

    # Simpan hasil transformasi
    dim_date.to_csv('/tmp/dim_date_payment.csv', index=False)
    dim_customer.to_csv('/tmp/dim_customer_payment.csv', index=False)
    dim_payment_method.to_csv('/tmp/dim_payment_method.csv', index=False)
    dim_coupon.to_csv('/tmp/dim_coupon.csv', index=False)
    fact_payment.to_csv('/tmp/fact_payment.csv', index=False)

# -----------------------
# LOAD
# -----------------------
def load():
    pd.read_csv('/tmp/dim_date_payment.csv').to_csv(os.path.join(dag_path, 'dim_date_payment.csv'), index=False)
    pd.read_csv('/tmp/dim_customer_payment.csv').to_csv(os.path.join(dag_path, 'dim_customer_payment.csv'), index=False)
    pd.read_csv('/tmp/dim_payment_method.csv').to_csv(os.path.join(dag_path, 'dim_payment_method.csv'), index=False)
    pd.read_csv('/tmp/dim_coupon.csv').to_csv(os.path.join(dag_path, 'dim_coupon.csv'), index=False)
    pd.read_csv('/tmp/fact_payment.csv').to_csv(os.path.join(dag_path, 'fact_payment.csv'), index=False)

# -----------------------
# DAG DEFINITION
# -----------------------
with DAG(
    dag_id='etl_fact_payment',
    start_date=datetime(2025, 6, 1),
    schedule='@daily',
    catchup=False,
    tags=['payment', 'fact_payment', 'etl']
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
