from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from datetime import datetime
from .models import PurchaseRecord

import numpy as np
from sklearn.linear_model import LinearRegression


# 🔹 View 1: Import CSV dan simpan ke DB, lalu tampilkan sebagai list
def purchase_list(request):
    # Baca file CSV (path relatif terhadap folder project)
    df = pd.read_csv('../transactions_ip.csv')

    # Hapus semua data lama dulu (opsional agar tidak duplikat)
    PurchaseRecord.objects.all().delete()

    for _, row in df.iterrows():
        PurchaseRecord.objects.create(
            transaction_id = row['transaction_id'],
            customer_id = row['customer_id'],
            transaction_date = datetime.strptime(row['transaction_date'], '%Y-%m-%d'),
            total_amount = row['total_amount'],
            payment_method = row['payment_method'],
            shipping_method = row['shipping_method'],
            delivery_time = row['delivery_time'],
            coupon_code = row['coupon_code'] if pd.notnull(row['coupon_code']) else "",
            city = row['city'],
            product_id = row['product_id'],
            sales_factor = row['sales_factor']
        )

    records = PurchaseRecord.objects.all()
    return render(request, 'purchase_list.html', {'records': records})

# 🔹 View 2: Tampilkan Chart Prediksi Penjualan
def purchase_chart(request):
    df = pd.DataFrame(list(PurchaseRecord.objects.all().values()))
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['Year'] = df['transaction_date'].dt.year
    df['Month'] = df['transaction_date'].dt.month

    summary = df.groupby(['Year', 'Month'])['total_amount'].sum().reset_index()

    X = []
    y = []
    for _, row in summary.iterrows():
        time = row['Year'] + (row['Month'] - 1) / 12
        X.append([time])
        y.append(row['total_amount'])

    X = np.array(X)
    y = np.array(y)

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    labels = [f"{row['Year']}-{int(row['Month']):02d}" for _, row in summary.iterrows()]

    return render(request, 'purchase_chart.html', {
        'labels': labels,
        'values': y.tolist(),
        'predictions': y_pred.tolist()
    })

def sales_by_city(request):
    df = pd.DataFrame(list(PurchaseRecord.objects.all().values()))
    city_sales = df.groupby('city')['total_amount'].sum().reset_index()

    labels = city_sales['city'].tolist()
    values = city_sales['total_amount'].tolist()

    return render(request, 'sales_by_city.html', {
        'labels': labels,
        'values': values
    })


# 🔹 View 3: Rata-rata Total Amount per Payment Method
def avg_payment_method(request):
    df = pd.DataFrame(list(PurchaseRecord.objects.all().values()))

    # Grouping berdasarkan metode pembayaran
    summary = df.groupby('payment_method')['total_amount'].mean().reset_index()
    labels = summary['payment_method'].tolist()
    values = summary['total_amount'].round(2).tolist()

    return render(request, 'avg_payment_chart.html', {
        'labels': labels,
        'values': values
    })

def shipping_duration_chart(request):
    df = pd.DataFrame(list(PurchaseRecord.objects.all().values()))

    # Asumsikan kolom delivery_time dalam format 'X days'
    df['duration'] = df['delivery_time'].str.extract(r'(\d+)').astype(float)
    
    summary = df.groupby('shipping_method')['duration'].mean().reset_index()

    labels = summary['shipping_method'].tolist()
    values = summary['duration'].round(2).tolist()

    return render(request, 'shipping_duration.html', {
        'labels': labels,
        'values': values
    })

def delivery_distribution(request):
    from django.db.models import Count
    from .models import PurchaseRecord

    data = (
        PurchaseRecord.objects
        .values('delivery_time')
        .annotate(jumlah=Count('id'))
        .order_by('delivery_time')
    )

    labels = [d['delivery_time'] for d in data]
    values = [d['jumlah'] for d in data]

    return render(request, 'delivery_distribution.html', {
        'labels': labels,
        'values': values
    })

# View: Rasio Penggunaan Kupon
def coupon_ratio_view(request):
    df = pd.DataFrame(list(PurchaseRecord.objects.all().values()))

    # Hitung jumlah kupon digunakan dan tidak digunakan
    total_with_coupon = df['coupon_code'].notna().sum()
    total_without_coupon = df['coupon_code'].isna().sum()

    return render(request, 'coupon_ratio.html', {
        'labels': ['Menggunakan Kupon', 'Tidak Menggunakan Kupon'],
        'values': [total_with_coupon, total_without_coupon]
    })