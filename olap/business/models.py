from django.db import models

class PurchaseRecord(models.Model):
    transaction_id = models.IntegerField()
    customer_id = models.IntegerField()
    transaction_date = models.DateField()
    total_amount = models.FloatField()
    payment_method = models.CharField(max_length=100)
    shipping_method = models.CharField(max_length=100)
    delivery_time = models.CharField(max_length=50)
    coupon_code = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100)
    product_id = models.IntegerField()
    sales_factor = models.FloatField()

    def __str__(self):
        return f"{self.city} - {self.transaction_date} - Rp{self.total_amount}"
