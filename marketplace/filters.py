import django_filters
from django.db.models.functions import Round
from .models import Item, Category


class ItemFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        field_name='categoryID',
        queryset=Category.objects.all(),
        label='Category',
        empty_label='All Categories',
    )
    min_price = django_filters.NumberFilter(
        method='filter_min_price',
        label='Min Price (Lek)',
    )
    max_price = django_filters.NumberFilter(
        method='filter_max_price',
        label='Max Price (Lek)',
    )
    condition = django_filters.ChoiceFilter(
        field_name='condition',
        choices=Item.CONDITION_CHOICES,
        empty_label='Any Condition',
        label='Condition',
    )
    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='icontains',
        label='City',
    )

    def filter_min_price(self, queryset, name, value):
        # Round the stored price to the nearest integer before comparing,
        # so items displayed as "1000 Lek" (via floatformat:0) are correctly
        # included when min_price=1000, even if stored as e.g. 999.9.
        return queryset.annotate(
            _price_rounded=Round('itemPrice')
        ).filter(_price_rounded__gte=float(value))

    def filter_max_price(self, queryset, name, value):
        return queryset.annotate(
            _price_rounded=Round('itemPrice')
        ).filter(_price_rounded__lte=float(value))

    class Meta:
        model = Item
        fields = ['category', 'condition', 'city']
