from django.urls import path

from products.views import ProductListView, UserBarUpdateView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("user_bars/update/", UserBarUpdateView.as_view(), name="user-bar-update"),
]

app_name = "products"
