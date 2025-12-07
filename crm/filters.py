import django_filters
from crm.models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    name_icontains = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email_icontains = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    created_at_gte = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    # Challenge: phone starts with pattern (e.g. +1)
    phone_pattern = django_filters.CharFilter(method="filter_phone_pattern")

    def filter_phone_pattern(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(phone__startswith=value)

    class Meta:
        model = Customer
        fields = []


class ProductFilter(django_filters.FilterSet):
    name_icontains = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    price_gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock_gte = django_filters.NumberFilter(field_name="stock", lookup_expr="gte")
    stock_lte = django_filters.NumberFilter(field_name="stock", lookup_expr="lte")

    # Optional helper: low stock (< 10)
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")

    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    class Meta:
        model = Product
        fields = []


class OrderFilter(django_filters.FilterSet):
    total_amount_gte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount_lte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    order_date_gte = django_filters.DateTimeFilter(field_name="order_date", lookup_expr="gte")
    order_date_lte = django_filters.DateTimeFilter(field_name="order_date", lookup_expr="lte")

    customer_name = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    product_name = django_filters.CharFilter(field_name="products__name", lookup_expr="icontains")

    # Challenge: orders that include a specific product id
    product_id = django_filters.NumberFilter(field_name="products__id", lookup_expr="exact")

    class Meta:
        model = Order
        fields = []
