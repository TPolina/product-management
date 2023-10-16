from django.core.validators import MinValueValidator
from rest_framework import serializers

from products.models import Product, UserBar, ProductImage


class ImageUrlRelatedField(serializers.RelatedField):
    """Custom related field to display a list of product image urls"""

    def to_representation(self, value: ProductImage) -> str:
        url = value.image.url
        request = self.context.get("request", None)
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class ProductSerializer(serializers.ModelSerializer):
    userbar_items_number = serializers.SerializerMethodField()
    images = ImageUrlRelatedField(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "userbar_items_number", "images")

    def get_userbar_items_number(self, obj: Product) -> int:
        request = self.context.get("request")
        user = request.user

        if user.is_authenticated:
            # we use all instead of get to decrease number of sql queries
            user_bars = obj.user_bars.all()

            if user_bars:
                return user_bars[0].items_number

        return 0


class UserBarSerializer(serializers.ModelSerializer):
    items_number = serializers.IntegerField(validators=(MinValueValidator(1),))

    class Meta:
        model = UserBar
        fields = ("product", "items_number")
