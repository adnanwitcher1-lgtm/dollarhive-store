# DollarHive 🐝 — "Smart Deals. More Savings."

A responsive eCommerce storefront built with:

- **Frontend:** HTML + Tailwind CSS (via CDN) + Bootstrap 5 (via CDN, for
  dropdowns/off-canvas mobile menu) + vanilla JavaScript
- **Backend:** Python / Django
- **Database:** SQLite

No React, no Node.js, no external JS build step required.

---

## 1. Project layout

```
dollarhive/
├── manage.py
├── requirements.txt
├── dollarhive/              # Django project package
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
└── store/                   # Django app: "store"
    ├── models.py            # Category, Product, Order, OrderItem
    ├── views.py             # home, shop, cart, checkout, etc.
    ├── urls.py
    ├── admin.py
    ├── cart.py              # session-based shopping cart
    ├── notifications.py     # email + WhatsApp order notifications
    ├── context_processors.py
    ├── management/commands/seed_store.py
    ├── templates/store/     # base.html, home.html, products.html, ...
    │   ├── partials/        # topbar, header, footer, product_card
    │   └── emails/          # plain-text email bodies
    └── static/store/        # css/style.css, js/main.js
```

---

## 2. Setup

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 2b. Copy the env template and fill in real values (email, Twilio, etc.)
cp .env.example .env

# 3. Run migrations (creates db.sqlite3)
python manage.py makemigrations
python manage.py migrate

# 4. Create an admin user (to manage products/categories/orders)
python manage.py createsuperuser

# 5. (Optional) seed some sample categories & products
python manage.py seed_store

# 6. Run the dev server
python manage.py runserver
```

Then visit:
- Storefront: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

Add product images from the admin panel — `Pillow` is already in
`requirements.txt` to support `ImageField`.

---

## 3. Static files

In development, Django serves `store/static/` automatically
(`STATICFILES_DIRS` in `settings.py` points to it) — nothing extra to
do. For production:

```bash
python manage.py collectstatic
```

This copies everything into `STATIC_ROOT` (`staticfiles/`), which
your web server (nginx, WhiteNoise, etc.) should then serve at the
`/static/` URL.

Uploaded media (product/category images) live under `media/` and are
served at `/media/` while `DEBUG = True`. In production, serve `media/`
from your web server or an object store (S3, etc.) instead.

---

## 4. Email notifications (order confirmation + merchant alert)

Two emails fire automatically the moment a customer completes
checkout (`store/notifications.py`, triggered from `views.checkout`):

1. **Customer confirmation** — order items, total, shipping info, sent
   to `order.customer_email`.
2. **Merchant alert** — sent to `settings.MERCHANT_EMAIL`.

By default, `EMAIL_BACKEND` is the **console backend** — emails print
straight into your terminal, so you can test the whole flow with zero
setup.

To send real email, edit `dollarhive/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'          # or your provider (SendGrid, Mailgun, SES...)
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'   # use an app password, not your real password
DEFAULT_FROM_EMAIL = 'orders@dollarhive.com'
MERCHANT_EMAIL = 'merchant@dollarhive.com'
```

Better: read these from environment variables (the settings file
already does this via `os.environ.get(...)` with safe fallbacks) —
just set the env vars instead of hardcoding secrets.

---

## 5. WhatsApp order notifications (Twilio)

`store/notifications.py` sends an instant WhatsApp receipt to the
customer and an alert to the merchant, using the **Twilio WhatsApp
Business API**.

1. Create a free account at https://www.twilio.com/
2. In the Twilio Console, activate the **WhatsApp Sandbox** (Messaging
   → Try it out → Send a WhatsApp message) for quick testing, or apply
   for a verified WhatsApp Business sender for production.
3. Grab your **Account SID** and **Auth Token** from the Twilio
   Console dashboard.
4. Set these environment variables (or edit `settings.py` directly):

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"     # Twilio sandbox number
export MERCHANT_WHATSAPP_NUMBER="whatsapp:+92XXXXXXXXXX" # your store's WhatsApp
```

5. Make sure `twilio` is installed (`pip install twilio` — already in
   `requirements.txt`).

If Twilio isn't configured, `notifications.py` skips WhatsApp sending
gracefully (logs a warning) instead of breaking checkout — so the
site still works fully with just email during local development.

**Where it's called:** all three notification triggers fire together
from a single call — `notify_new_order(order)` — inside
`store/views.py::checkout()`, right after the `Order` and its
`OrderItem`s are saved.

---

## 6. Key URLs

| URL                          | View               | Purpose                          |
|-------------------------------|--------------------|-----------------------------------|
| `/`                           | `home`             | Hero, categories, deals grid      |
| `/shop/`                      | `products`         | Full product grid + filters       |
| `/deals/`                     | `deals`            | Discounted products only          |
| `/new-arrivals/`               | `new_arrivals`     | Newest products                   |
| `/product/<slug>/`            | `product_detail`   | Single product page               |
| `/cart/`                      | `cart_detail`      | Cart page                         |
| `/checkout/`                  | `checkout`         | Checkout form + order placement   |
| `/order/success/<id>/`        | `order_success`    | Post-checkout confirmation        |
| `/track-order/`               | `track_order`      | Order lookup by ID + email        |
| `/about-us/`, `/contact-us/`  | `about`, `contact` | Static pages                      |
| `/admin/`                     | Django admin        | Manage categories/products/orders |

---

## 7. Notes for going to production

- Set `DEBUG = False` and a real, secret `SECRET_KEY` (env var). Done
  automatically here — see `.env.example`.
- Set `ALLOWED_HOSTS` to your real domain(s) — via `DJANGO_ALLOWED_HOSTS`.
- Postgres is used automatically in production when `DATABASE_URL` is
  set (Render's free Postgres add-on sets this for you) — SQLite stays
  the default for local dev.
- Wire up a real payment gateway in `checkout.html` / `views.checkout`
  (currently Cash-on-Delivery only, as a placeholder).
- Static files are served by **WhiteNoise** (already wired into
  `MIDDLEWARE` + `STORAGES`) — no separate CDN needed for a small store.
- Product/category images uploaded through the admin panel **after**
  deploy will be lost on the next redeploy — Render's disk isn't
  persistent on the free plan. For a real store, add a Render paid
  "Disk" or switch `MEDIA` storage to S3/Cloudinary. Fine for a demo.

---

## 8. Push to GitHub

```bash
cd dollarhive              # this folder (the one with manage.py)
git init
git add .
git commit -m "Initial commit — DollarHive storefront"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

If you don't have a repo yet: create one at https://github.com/new
(don't initialize it with a README — this project already has one),
then use the URL it gives you above.

**Before pushing:** double-check `.env` is NOT tracked
(`git status` should not show it — `.gitignore` already excludes it).

---

## 9. Deploy to Render (whole app — frontend + backend + admin)

This is one Django app, so it deploys as a single Render **Web
Service** (no separate frontend/backend split needed).

1. Go to https://dashboard.render.com/ → **New +** → **Web Service**.
2. Connect your GitHub account and pick this repo.
3. Settings:
   - **Root Directory:** leave blank if you pushed the `dollarhive/`
     folder itself as the repo root (recommended above).
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput
     ```
   - **Start Command:**
     ```
     gunicorn dollarhive.wsgi:application --bind 0.0.0.0:$PORT
     ```
4. Add environment variables (Render dashboard → your service →
   **Environment**):

   | Key | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | a long random string |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `your-app-name.onrender.com` |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` |
   | `EMAIL_HOST_USER` | your Gmail address |
   | `EMAIL_HOST_PASSWORD` | your Gmail app password |
   | `MERCHANT_EMAIL` | inbox for order alerts |
   | `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | (optional, WhatsApp) |

   (Optional but recommended) Also add a free **Render Postgres**
   database from the dashboard, then copy its **Internal Database
   URL** into an env var named `DATABASE_URL` — this makes your data
   survive redeploys, unlike SQLite.

5. Click **Create Web Service**. Render will build and deploy — first
   deploy takes a few minutes.
6. Once live, open the Render **Shell** tab (or add a one-off job) and run:
   ```
   python manage.py createsuperuser
   python manage.py seed_store   # optional demo data
   ```
7. Visit `https://your-app-name.onrender.com/` for the store and
   `/admin/` for the admin panel, logging in with the superuser you
   just created.

That's it — storefront, checkout, and the Django admin panel are all
live on the same URL.
