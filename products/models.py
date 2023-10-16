from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint


class User(AbstractUser):
    pass


class Product(models.Model):
    name = models.CharField(max_length=255)
    in_trash = models.BooleanField()

    def __str__(self) -> str:
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    # Currently images are saved locally in the root folder.
    # Should be customized for the production
    image = models.ImageField()

    def __str__(self) -> str:
        return self.image.name


class UserBar(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="user_bars"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="user_bars"
    )
    items_number = models.IntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "product"], name="unique_user_product_combination"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.product.name}: {self.items_number}"
