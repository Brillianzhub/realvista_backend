from django.urls import path
from . import views

urlpatterns = [
    path("boost-packages/", views.list_boost_packages, name="boost-packages"),
    path("boost-order/", views.create_boost_order, name="create-boost-order"),
]
