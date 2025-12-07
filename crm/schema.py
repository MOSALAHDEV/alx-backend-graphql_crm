import re
from decimal import Decimal

import graphene
from django.db import transaction
from django.utils import timezone
from graphene_django import DjangoObjectType
from graphql import GraphQLError

from crm.models import Customer, Product, Order


# -------------------------
# GraphQL Types
# -------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# -------------------------
# Query
# -------------------------
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.select_related("customer").prefetch_related("products").all()


# -------------------------
# Inputs
# -------------------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


# -------------------------
# Helpers (Validation)
# -------------------------
PHONE_PATTERNS = (
    re.compile(r"^\+\d{10,15}$"),          # +1234567890 (10-15 digits)
    re.compile(r"^\d{3}-\d{3}-\d{4}$"),    # 123-456-7890
)

def validate_phone(phone: str) -> None:
    if phone is None or phone == "":
        return
    if not any(p.match(phone) for p in PHONE_PATTERNS):
        raise GraphQLError("Invalid phone format. Use +1234567890 or 123-456-7890.")

def validate_unique_email(email: str) -> None:
    if Customer.objects.filter(email=email).exists():
        raise GraphQLError("Email already exists.")


# -------------------------
# Mutations
# -------------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input: CustomerInput):
        name = input.get("name")
        email = input.get("email")
        phone = input.get("phone")

        validate_unique_email(email)
        validate_phone(phone)

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        created = []
        errors = []

        # Partial success: each record uses its own transaction
        for idx, c in enumerate(input):
            name = c.get("name")
            email = c.get("email")
            phone = c.get("phone")

            try:
                validate_unique_email(email)
                validate_phone(phone)

                with transaction.atomic():
                    customer = Customer.objects.create(name=name, email=email, phone=phone)
                    created.append(customer)
            except Exception as e:
                errors.append(f"Record {idx}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input: ProductInput):
        name = input.get("name")
        price = input.get("price")
        stock = input.get("stock", 0)

        # Validate
        if price is None:
            raise GraphQLError("Price is required.")
        try:
            price_dec = Decimal(str(price))
        except Exception:
            raise GraphQLError("Invalid price value.")

        if price_dec <= 0:
            raise GraphQLError("Price must be positive.")
        if stock is None:
            stock = 0
        if int(stock) < 0:
            raise GraphQLError("Stock must be non-negative.")

        product = Product.objects.create(name=name, price=price_dec, stock=int(stock))
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    def mutate(root, info, input: OrderInput):
        customer_id = input.get("customer_id")
        product_ids = input.get("product_ids") or []
        order_date = input.get("order_date") or timezone.now()

        if not product_ids:
            raise GraphQLError("At least one product must be selected.")

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Invalid customer ID.")

        products = list(Product.objects.filter(pk__in=product_ids))
        if len(products) != len(set(product_ids)):
            raise GraphQLError("Invalid product ID in productIds.")

        total = sum((p.price for p in products), Decimal("0.00"))

        with transaction.atomic():
            order = Order.objects.create(customer=customer, total_amount=total, order_date=order_date)
            order.products.set(products)

        return CreateOrder(order=order)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
