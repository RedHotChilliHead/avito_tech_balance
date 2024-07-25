from django.db import models


class Customer(models.Model):
    """
    Модель пользователя (для создания schema.sql)
    """
    class Meta:
        ordering = ['id']
    name = models.CharField(max_length=100, blank=False)
    balance = models.DecimalField(max_digits=99, decimal_places=2, blank=False, null=False, default=0)


class Transaction(models.Model):
    """
    Модель транзакции (для создания schema.sql)
    """
    class Meta:
        ordering = ['id']
    amount = models.DecimalField(max_digits=99, decimal_places=2)
    timestamp = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=150, blank=True, null=True)
    sender = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True,
                               related_name='sent_transactions')  # отправитель
    recipient = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True,
                                  related_name='received_transactions')  # получатель

# python manage.py sqlmigrate balanceapp > schema.sql

