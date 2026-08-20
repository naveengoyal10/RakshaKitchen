from django.urls import path

from . import views

app_name = "kitchen"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("menu/", views.menu, name="menu"),
    path("menu/<slug:slug>/", views.menu_detail, name="menu_detail"),
    path("menu-pricing/", views.menu_pricing, name="menu_pricing"),
    path("bulk-orders/", views.bulk_orders, name="bulk_orders"),
    path("contact/", views.contact, name="contact"),
    path("robots.txt", views.robots, name="robots"),
    path("order/", views.order, name="order"),
    path("order/success", views.order_success, name="order_success"),
]
