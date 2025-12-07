import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql.settings")
django.setup()

from crm.models import Customer, Product, Order  # noqa: E402


def run():
    # Customers
    alice, _ = Customer.objects.get_or_create(
        email="alice@example.com",
        defaults={"name": "Alice", "phone": "+1234567890"},
    )
    bob, _ = Customer.objects.get_or_create(
        email="bob@example.com",
        defaults={"name": "Bob", "phone": "123-456-7890"},
    )

    # Products
    laptop, _ = Product.objects.get_or_create(
        name="Laptop",
        defaults={"price": Decimal("999.99"), "stock": 10},
    )
    mouse, _ = Product.objects.get_or_create(
        name="Mouse",
        defaults={"price": Decimal("25.00"), "stock": 50},
    )

    # Order
    order = Order.objects.create(customer=alice, total_amount=Decimal("0.00"))
    order.products.set([laptop, mouse])
    order.total_amount = laptop.price + mouse.price
    order.save()

    print("Seed complete:")
    print(f"- Customers: {Customer.objects.count()}")
    print(f"- Products: {Product.objects.count()}")
    print(f"- Orders: {Order.objects.count()}")


if __name__ == "__main__":
    run()
