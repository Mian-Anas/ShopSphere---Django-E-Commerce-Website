"""
Store URLs.
"""
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('shop/', views.shop_view, name='shop'),
    path('shop/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('shop/<slug:slug>/review/', views.submit_review_view, name='submit_review'),
    path('api/search/', views.search_api_view, name='search_api'),
]
