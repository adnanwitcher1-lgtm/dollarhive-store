"""
A small session-backed shopping cart. No external packages needed —
keeps the tech stack to plain Django as required by the brief.

Session shape:
    request.session['cart'] = {
        '<product_id>': quantity,
        ...
    }
"""
from decimal import Decimal

from .models import Product

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id] += quantity
        else:
            self.cart[product_id] = quantity
        self.save()

    def set_quantity(self, product, quantity):
        product_id = str(product.id)
        if quantity <= 0:
            self.remove(product)
            return
        self.cart[product_id] = quantity
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        """Yields dicts with product, quantity, and line_total for
        each item currently in the cart."""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_map = {str(p.id): p for p in products}

        for product_id, quantity in self.cart.items():
            product = products_map.get(product_id)
            if not product:
                continue
            yield {
                'product': product,
                'quantity': quantity,
                'line_total': product.price * quantity,
            }

    def __len__(self):
        return len(self.cart)

    @property
    def total_quantity(self):
        return sum(self.cart.values())

    @property
    def total_price(self):
        return sum(Decimal(item['line_total']) for item in self)
