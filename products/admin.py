from django.contrib import admin

from products.models import Product, ProductImage, UserBar, User

admin.site.register(User)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(UserBar)
