"""
DollarHive store views.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .cart import Cart
from .wishlist import Wishlist
from .models import Category, Product, Order, OrderItem
from .notifications import notify_new_order


# ----------------------------------------------------------------------
# Home
# ----------------------------------------------------------------------
def home(request):
    """Landing page: hero banner, value props, categories, product grid."""
    categories = Category.objects.all()[:8]
    featured_products = Product.objects.filter(is_featured=True)[:8]
    deal_products = (
        Product.objects.filter(discount_price__isnull=False)
        .order_by('-created_at')[:8]
    )
    new_arrivals = Product.objects.order_by('-created_at')[:8]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'deal_products': deal_products,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'store/home.html', context)


# ----------------------------------------------------------------------
# Shop / product grid with category + price filtering
# ----------------------------------------------------------------------
def products(request):
    """The main Shop page: filterable / searchable product grid."""
    product_list = Product.objects.select_related('category').all()
    categories = Category.objects.all()

    # --- search ---
    query = request.GET.get('q', '').strip()
    if query:
        product_list = product_list.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # --- category filter ---
    category_slug = request.GET.get('category', '')
    active_category = None
    if category_slug:
        active_category = categories.filter(slug=category_slug).first()
        if active_category:
            product_list = product_list.filter(category=active_category)

    # --- price range filter ---
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    try:
        if min_price:
            product_list = product_list.filter(price__gte=Decimal(min_price))
        if max_price:
            product_list = product_list.filter(price__lte=Decimal(max_price))
    except InvalidOperation:
        pass  # ignore malformed price input rather than 500

    # --- sort ---
    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-rating',
    }
    product_list = product_list.order_by(sort_map.get(sort, '-created_at'))

    context = {
        'products': product_list,
        'categories': categories,
        'active_category': active_category,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    }
    return render(request, 'store/products.html', context)


def deals(request):
    """"Deals" nav link: products currently marked down."""
    product_list = (
        Product.objects.filter(discount_price__isnull=False)
        .order_by('-created_at')
    )
    return render(request, 'store/products.html', {
        'products': product_list,
        'categories': Category.objects.all(),
        'page_title': 'Today\u2019s Deals',
    })


def new_arrivals(request):
    """"New Arrivals" nav link: most recently added products."""
    product_list = Product.objects.order_by('-created_at')
    return render(request, 'store/products.html', {
        'products': product_list,
        'categories': Category.objects.all(),
        'page_title': 'New Arrivals',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(pk=product.pk)[:4]
    )
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


# ----------------------------------------------------------------------
# Cart
# ----------------------------------------------------------------------
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1) or 1)
    Cart(request).add(product, quantity=quantity)
    messages.success(request, f'Added "{product.name}" to your cart.')

    next_url = request.POST.get('next') or 'store:products'
    return redirect(next_url)


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get('quantity', 1) or 1)
    Cart(request).set_quantity(product, quantity)
    return redirect('store:cart_detail')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    Cart(request).remove(product)
    messages.info(request, f'Removed "{product.name}" from your cart.')
    return redirect('store:cart_detail')


# ----------------------------------------------------------------------
# Wishlist
# ----------------------------------------------------------------------
def wishlist_detail(request):
    wishlist = Wishlist(request)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist})


@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    now_saved = Wishlist(request).toggle(product)
    if now_saved:
        messages.success(request, f'Added "{product.name}" to your wishlist.')
    else:
        messages.info(request, f'Removed "{product.name}" from your wishlist.')

    next_url = request.POST.get('next') or 'store:wishlist_detail'
    return redirect(next_url)


@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    Wishlist(request).remove(product)
    messages.info(request, f'Removed "{product.name}" from your wishlist.')
    return redirect('store:wishlist_detail')


# ----------------------------------------------------------------------
# Checkout & order placement
# ----------------------------------------------------------------------
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty — add a few great deals first!')
        return redirect('store:products')

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        shipping_city = request.POST.get('shipping_city', '').strip()
        shipping_country = request.POST.get('shipping_country', '').strip()

        if not (customer_name and customer_email and customer_phone and shipping_address):
            messages.error(request, 'Please fill in all required fields to place your order.')
            return render(request, 'store/checkout.html', {'cart': cart})

        # --- create the order + snapshot each cart line as an OrderItem ---
        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_country=shipping_country,
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                product_name=item['product'].name,
                price=item['product'].price,
                quantity=item['quantity'],
            )

        order.recalculate_total()

        # --- fire all three notification triggers (email x2 + WhatsApp) ---
        notify_new_order(order)

        cart.clear()
        return redirect('store:order_success', order_id=order.pk)

    return render(request, 'store/checkout.html', {'cart': cart})


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'store/order_success.html', {'order': order})


def track_order(request):
    order = None
    searched = False
    if request.method == 'POST':
        searched = True
        order_id = request.POST.get('order_id', '').strip()
        email = request.POST.get('email', '').strip()
        order = Order.objects.filter(pk=order_id, customer_email__iexact=email).first()
        if not order:
            messages.error(request, 'No matching order found. Double check your Order ID and email.')

    return render(request, 'store/track_order.html', {'order': order, 'searched': searched})


# ----------------------------------------------------------------------
# Static info pages
# ----------------------------------------------------------------------
def about(request):
    return render(request, 'store/about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thanks for reaching out! Our support team will reply within 24 hours.')
        return redirect('store:contact')
    return render(request, 'store/contact.html')
