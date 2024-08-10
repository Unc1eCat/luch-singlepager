from datetime import timedelta
from typing import Iterable, Optional
from django.db import models as m
from django.urls import reverse
from django.utils.timezone import now
from django.core.validators import RegexValidator
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
import secrets
from django.contrib.sessions.models import Session


VKEY_VALIDATOR = RegexValidator(r'^[A-Z0-9]{32}$')


class OrderStatus(m.IntegerChoices):
    AWAITING_EMAIL_VERIFICATION = 0
    AWAITING_REVIEW = 1
    AWAITING_DELIVERY = 2
    DELIVERING = 3
    DELIVERED = 4
    RECEIVED = 5
    CANCELED = 6


RECEIVED_STATUSES = {OrderStatus.RECEIVED}
STARTED_DELIVERY_STATUSES = {OrderStatus.DELIVERING, OrderStatus.DELIVERED}

# Number of decimal places to display in quantity of a product for each unit a product can have
unit_quantity_decimal_places = {
    "kg": 1,  # kilograms
    "it.": 0,  # items
}


class Product(m.Model):
    title = m.CharField(max_length=64)
    unit = m.CharField(max_length=8)
    price = m.FloatField()  # Per one unit
    active = m.BooleanField(blank=True, default=True)


class Order(m.Model):
    status = m.IntegerField(choices=OrderStatus.choices, blank=True, default=OrderStatus.AWAITING_REVIEW)
    created_timestamp = m.DateTimeField(auto_now_add=True, blank=True)
    started_delivery_timestamp = m.DateTimeField(blank=True, null=True)
    received_timestamp = m.DateTimeField(blank=True, null=True)

    phone_number = m.CharField(max_length=19, validators=[RegexValidator(r'^\d{3,19}$')])
    email = m.EmailField()
    first_name = m.CharField(max_length=22)
    last_name = m.CharField(max_length=22)
    address = m.CharField(max_length=120, blank=True, null=True)

    # This field is here in case the cost must differ from the intuitive total cost of all items
    cost = m.DecimalField(decimal_places=2, max_digits=16, blank=True)

    @property
    def is_email_verified(self):
        return self.status != OrderStatus.AWAITING_EMAIL_VERIFICATION and self.status != None

    def get_natural_cost(self):
        return self.items_set.annotate(cost=F('product.price') * F('quantity')).aggregate(Sum('cost'))['cost__sum']

    def save(self, *args, **kwargs) -> None:
        if self.status in STARTED_DELIVERY_STATUSES and self.started_delivery_timestamp is None:
            self.started_delivery_timestamp = now()
        if self.status in RECEIVED_STATUSES and self.received_timestamp is None:
            self.received_timestamp = now()

        if self.cost is None:
            # If there is pk then there is such object in DB. If there is no such object in DB then there are probably no items for that order therefore the cost is probably 0.
            # TODO: Connect to signal to calculate cost after the object is saved
            self.cost = self.get_natural_cost() if self.pk else 0

        super().save(*args, **kwargs)


class OrderedItem(m.Model):
    order = m.ForeignKey(to=Order, on_delete=m.CASCADE, related_name="items_set")
    product = m.ForeignKey(to=Product, on_delete=m.CASCADE)

    quantity = m.FloatField()

    def get_cost(self):
        return self.product.price * self.quantity


def order_access_key_default_key():
    return secrets.token_bytes(32)


class OrderAccessKey(m.Model):
    email = m.EmailField()

    key = m.BinaryField(max_length=32, default=order_access_key_default_key)
    creation_timestamp = m.DateTimeField(auto_now_add=True)
    forcibly_invalid = m.BooleanField(default=False)
    session = m.ForeignKey(Session, null=True, blank=True, on_delete=m.CASCADE)

    @property
    def expiry_timestamp(self):
        return self.creation_timestamp + timedelta(hours=4)

    @property
    def is_valid(self):
        return not self.forcibly_invalid and self.expiry_timestamp < now()

    def get_url(self, order=None):
        """ If `order` is None then returns the URL for the corresponding email page, else return the URL for specified order. """
        if order is None:
            ret = reverse('orders_for_email', kwargs={'email': self.email})
        else:
            ret = reverse('order', kwargs={'pk': order.pk})
        return ret + f'?key={self.key}'
