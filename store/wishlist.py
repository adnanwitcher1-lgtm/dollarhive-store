"""
A small session-backed wishlist. Mirrors the pattern used by cart.py —
no external packages, no DB model/migration needed. Works for guests
and logged-in visitors alike, tied to their browser session.

Session shape:
    request.session['wishlist'] = ['<product_id>', '<product_id>', ...]
"""
from .models import Product

WISHLIST_SESSION_KEY = 'wishlist'


class Wishlist:
    def __init__(self, request):
        self.session = request.session
        wishlist = self.session.get(WISHLIST_SESSION_KEY)
        if wishlist is None:
            wishlist = self.session[WISHLIST_SESSION_KEY] = []
        self.wishlist = wishlist

    def add(self, product):
        product_id = str(product.id)
        if product_id not in self.wishlist:
            self.wishlist.append(product_id)
            self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.wishlist:
            self.wishlist.remove(product_id)
            self.save()

    def toggle(self, product):
        """Adds the product if it's not in the wishlist, removes it if
        it is. Returns True if it's now in the wishlist, False if it
        was just removed."""
        product_id = str(product.id)
        if product_id in self.wishlist:
            self.wishlist.remove(product_id)
            self.save()
            return False
        self.wishlist.append(product_id)
        self.save()
        return True

    def clear(self):
        self.session[WISHLIST_SESSION_KEY] = []
        self.save()

    def save(self):
        self.session.modified = True

    def __contains__(self, product_id):
        return str(product_id) in self.wishlist

    def __iter__(self):
        products = Product.objects.filter(id__in=self.wishlist)
        products_map = {str(p.id): p for p in products}
        for product_id in self.wishlist:
            product = products_map.get(product_id)
            if product:
                yield product

    def __len__(self):
        return len(self.wishlist)
