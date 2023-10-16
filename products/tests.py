from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from products.models import Product, ProductImage, UserBar
from products.serializers import ProductSerializer
from products.views import ProductListView

PRODUCT_LIST_URL = reverse("products:product-list")
USER_BAR_UPDATE_URL = reverse("products:user-bar-update")


def create_sample_user(**params) -> get_user_model():
    defaults = {
        "username": "testusername",
        "password": "testpassword123",
    }
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_sample_product(**params) -> Product:
    defaults = {
        "name": "test",
        "in_trash": False,
    }
    defaults.update(params)

    return Product.objects.create(**defaults)


def create_sample_image(product: Product, **params) -> ProductImage:
    defaults = {"image": "test.jpg"}
    defaults.update(params)

    return ProductImage.objects.create(product=product, **defaults)


def creare_sample_userbar(
    user: get_user_model(), product: Product, **params
) -> UserBar:
    defaults = {"items_number": 2}
    defaults.update(params)

    return UserBar.objects.create(user=user, product=product, **defaults)


class ProductListTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.view = ProductListView.as_view()
        self.user = create_sample_user()

    def test_unauthenticated_list_products(self) -> None:
        create_sample_product()
        product_with_images = create_sample_product(name="test2")

        create_sample_image(product_with_images)
        create_sample_image(product_with_images, image="test2.jpg")

        request = self.factory.get(PRODUCT_LIST_URL)
        response = self.view(request)

        products = Product.objects.all()
        serializer = ProductSerializer(
            products, many=True, context={"request": request}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(response.data["results"], serializer.data)
        self.assertEqual(response.data["results"][0]["userbar_items_number"], 0)

    def test_in_trash_products_not_listed(self) -> None:
        product = create_sample_product()
        product_in_trash = create_sample_product(in_trash=True)

        request = self.factory.get(PRODUCT_LIST_URL)
        response = self.view(request)

        product_serializer = ProductSerializer(product, context={"request": request})
        product_in_trash_serializer2 = ProductSerializer(
            product_in_trash, context={"request": request}
        )

        self.assertIn(product_serializer.data, response.data["results"])
        self.assertNotIn(product_in_trash_serializer2.data, response.data["results"])

    def test_correct_userbar_items_number_for_authenticated_user(self) -> None:
        product = create_sample_product()
        user_bar = creare_sample_userbar(user=self.user, product=product)

        create_sample_product(name="test2")

        request = self.factory.get(PRODUCT_LIST_URL)
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0]["userbar_items_number"], user_bar.items_number
        )
        self.assertEqual(response.data["results"][1]["userbar_items_number"], 0)

    def test_only_userbars_of_authenticated_user_are_taken(self) -> None:
        product = create_sample_product()
        user_bar = creare_sample_userbar(user=self.user, product=product)

        another_user = create_sample_user(username="another_user")
        another_product = create_sample_product(name="another")
        creare_sample_userbar(user=another_user, product=another_product)

        request = self.factory.get(PRODUCT_LIST_URL)
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            response.data["results"][0]["userbar_items_number"], user_bar.items_number
        )
        self.assertEqual(response.data["results"][1]["userbar_items_number"], 0)


class UserBarUpdateTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_sample_user()
        self.client.force_authenticate(self.user)

    def test_update_existing_userbar(self) -> None:
        product = create_sample_product()
        creare_sample_userbar(user=self.user, product=product)
        new_items_number = 10

        payload = {"product": product.id, "items_number": new_items_number}

        response = self.client.put(USER_BAR_UPDATE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_bar = UserBar.objects.get(user=self.user, product=product)
        self.assertEqual(user_bar.items_number, new_items_number)

    def test_create_new_userbar_if_not_exist(self) -> None:
        product = create_sample_product()
        new_items_number = 10

        payload = {"product": product.id, "items_number": new_items_number}

        response = self.client.put(USER_BAR_UPDATE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_bar = UserBar.objects.get(user=self.user, product=product)
        self.assertEqual(user_bar.items_number, new_items_number)

    def test_items_number_should_be_lg_0(self) -> None:
        product = create_sample_product()

        payload = {"product": product.id, "items_number": 0}

        response = self.client.put(USER_BAR_UPDATE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
