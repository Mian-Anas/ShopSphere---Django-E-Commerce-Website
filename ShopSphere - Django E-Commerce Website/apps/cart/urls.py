"""
Cart URLs.
"""
from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='cart'),
    path('add/', views.add_to_cart_view, name='add'),
    path('update/', views.update_cart_view, name='update'),
    path('remove/', views.remove_from_cart_view, name='remove'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart_view, name='move_to_cart'),
]
