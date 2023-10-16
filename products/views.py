from django.db.models import Prefetch, QuerySet
from django.http import HttpRequest
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import Product, UserBar
from products.serializers import ProductSerializer, UserBarSerializer


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self) -> QuerySet:
        queryset = Product.objects.filter(in_trash=False).prefetch_related("images")
        user = self.request.user

        if user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch("user_bars", queryset=UserBar.objects.filter(user=user))
            )

        return queryset


class UserBarUpdateView(generics.UpdateAPIView):
    queryset = UserBar.objects.all()
    serializer_class = UserBarSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> UserBar | None:
        """Get UserBar object if exists"""
        user = self.request.user
        product_id = self.request.data.get("product")

        user_bar = UserBar.objects.filter(user=user, product_id=product_id)

        return user_bar[0] if user_bar else None

    def update(self, request: HttpRequest, *args, **kwargs) -> Response:
        """
        Update UserBar object with default update method if it exists.
        Create new UserBar object for current user.
        We use request.user so that user cannot see other users.
        Also, the check that product is not in trash should be added.
        """
        if self.get_object():
            return super().update(request, *args, **kwargs)

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
