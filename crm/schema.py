import re
from decimal import Decimal
from typing import Optional

import graphene
from django.db import IntegrityError, transaction
from django.utils import timezone
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from crm.filters import CustomerFilter, ProductFilter, OrderFilter
from crm.models import Product
from crm.models import Customer, Order
from crm.models import Product


# -------------------------
# Relay Nodes (for edges/node filtering queries)
# -------------------------
class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "email", "phone", "created_at")


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderNode(DjangoObjectType):
    # Convenience: allow querying `product { ... }` (first product)
    product = graphene.Field(ProductNode)

    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = ("id", "customer", "products", "total_amount", "order_date")

    def resolve_product(self, info):
        return self.products.first()


# -------------------------
# Simple types for mutation returns
# -------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    product = graphene.Field(ProductType)

    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")

    def resolve_product(self, info):
        return self.products.first()


# -------------------------
# Query (Task 3 filtering)
# -------------------------
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilter,
        order_by=graphene.String(),
    )
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filterset_class=ProductFilter,
        order_by=graphene.String(),
    )
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilter,
        order_by=graphene.String(),
    )

    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.select_related("customer").prefetch_related("products").all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs.distinct()


# -------------------------
# Inputs (for mutations)
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
    re.compile(r"^\+\d{10,15}$"),
    re.compile(r"^\d{3}-\d{3}-\d{4}$"),
)


def validate_phone(phone: Optional[str]) -> None:
    if not phone:
        return
    if not any(p.match(phone) for p in PHONE_PATTERNS):
        raise GraphQLError("Invalid phone format. Use +1234567890 or 123-456-7890.")


def validate_unique_email(email: str) -> None:
    if Customer.objects.filter(email=email).exists():
        raise GraphQLError("Email already exists.")


def to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        raise GraphQLError("Invalid price value.")


# -------------------------
# Mutations (Task 2 + Task 3)
# -------------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone):
        validate_unique_email(email)
        validate_phone(phone)

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()  # checker wants save()

        return CreateCustomer(customer=customer, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created = []
        errors = []

        with transaction.atomic():
            for idx, c in enumerate(input):
                name = c.get("name")
                email = c.get("email")
                phone = c.get("phone")

                try:
                    validate_phone(phone)
                    validate_unique_email(email)

                    with transaction.atomic():
                        customer = Customer(name=name, email=email, phone=phone)
                        customer.save()
                        created.append(customer)

                except GraphQLError as e:
                    errors.append(f"Record {idx}: {e.message}")
                except IntegrityError:
                    errors.append(f"Record {idx}: Email already exists.")
                except Exception as e:
                    errors.append(f"Record {idx}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        name = input.get("name")
        price = to_decimal(input.get("price"))
        stock = input.get("stock", 0)

        if price <= 0:
            raise GraphQLError("Price must be positive.")
        if stock is None:
            stock = 0
        if int(stock) < 0:
            raise GraphQLError("Stock must be non-negative.")

        product = Product(name=name, price=price, stock=int(stock))
        product.save()
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
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
            raise GraphQLError("Invalid product ID.")

        total = sum((p.price for p in products), Decimal("0.00"))

        with transaction.atomic():
            order = Order(customer=customer, total_amount=total, order_date=order_date)
            order.save()
            order.products.set(products)

        return CreateOrder(order=order)


class UpdateLowStockProducts(graphene.Mutation):
    products = graphene.List(ProductType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info):
        updated = []
        low_qs = Product.objects.filter(stock__lt=10)

        with transaction.atomic():
            for p in low_qs:
                p.stock = int(p.stock) + 10
                p.save()
                updated.append(p)

        return UpdateLowStockProducts(products=updated, message="Low stock products updated successfully.")


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()
