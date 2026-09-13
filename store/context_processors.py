"""
Makes the cart item count available in every template as
{{ CART_ITEM_COUNT }}, so the yellow badge on the header cart icon
always stays accurate without every view having to pass it manually.
Also exposes the wishlist badge/state and a ready-to-use WhatsApp
click-to-chat link built from settings.MERCHANT_WHATSAPP_NUMBER.
"""
import re

from django.conf import settings

from .cart import Cart
from .wishlist import Wishlist
from .models import Category


def cart_item_count(request):
    """Exposes the cart badge count, wishlist badge/ids, the full
    category list (for the "All Categories" dropdown + footer), and
    the merchant's WhatsApp chat link to every template."""
    wishlist = Wishlist(request)

    # settings.MERCHANT_WHATSAPP_NUMBER looks like 'whatsapp:+923001234567'.
    # wa.me links need just the digits (no '+', no 'whatsapp:' prefix).
    raw_number = getattr(settings, 'MERCHANT_WHATSAPP_NUMBER', '') or ''
    digits_only = re.sub(r'\D', '', raw_number)
    whatsapp_link = f'https://wa.me/{digits_only}' if digits_only else ''

    return {
        'CART_ITEM_COUNT': Cart(request).total_quantity,
        'WISHLIST_ITEM_COUNT': len(wishlist),
        'WISHLIST_PRODUCT_IDS': {int(pid) for pid in wishlist.wishlist},
        'MERCHANT_WHATSAPP_LINK': whatsapp_link,
        'NAV_CATEGORIES': Category.objects.all(),
    }
