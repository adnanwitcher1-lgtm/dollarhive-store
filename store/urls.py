from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.products, name='products'),
    path('deals/', views.deals, name='deals'),
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),

    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('track-order/', views.track_order, name='track_order'),

    path('about-us/', views.about, name='about'),
    path('contact-us/', views.contact, name='contact'),
]
