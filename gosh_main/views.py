from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
import logging
import re
import random  
from django.contrib import messages
from types import SimpleNamespace
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import PasswordResetRequestForm
from .services.email_service import (
    send_contact_email,
    send_password_reset_email,
    send_email_verification_email,
)

from django.http import JsonResponse
from django.db.models import Sum
from .models import RestaurantOrder

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()
EXCLUDED_CATEGORY_SLUGS = {'staples', 'oils', 'flours'}

CATEGORY_DISPLAY_NAMES = {
    'vegetable-leaves': 'African Vegetable Leaves & Pods',
    'staples-thickeners': 'African Staples & Thickeners',
    'seafoods': 'African Seafoods',
    'plant-milk': 'African Plant-Milk Beverages',
    'oils-fats': 'Natural African Edible Oils & Fats',
    'flours-grains': 'African Flours & Grains',
    'spices': 'African Spices & Seasonings',
    'juices': 'Natural Juices & Beverages',
    'water': 'Packaged Drinking Water',
    'animal-feeds': 'Animal Feeds',
}

UNIT_LABELS = {
    'item': 'item',
    'kg': 'kg',
    'g': 'g',
    'l': 'L',
    'ml': 'ml',
    'bag': 'bag',
    'bottle': 'bottle',
    'pack': 'pack',
}

GENERIC_CATEGORY_IMAGE_NAMES = {
    'product2.jpg',
    'product4.jpg',
    'product5.jpg',
    'product6.jpg',
    'feature_1.jpg',
    'feature_2.jpg',
    'feature_3.jpg',
}

PRODUCT_SLUG_IMAGE_FALLBACKS = {
    'dried-ukazi-afang-leaf-1kg': 'dried_afang.jpg',
    'dried-bitter-leaf-1kg': 'dried_bitter_leaf.jpg',
    'dried-ugu-fluted-pumpkin-1kg': 'dried_ugu.jpg',
    'dried-utazi-leaf-1kg': 'dried_utazi.jpg',
    'ground-melon-egusi-1kg': 'ground_melon.jpg',
    'whole-melon-egusi-seeds-5kg': 'whole_melon_seeds.jpg',
    'ground-ogbono-seeds-1kg': 'ground_ogbono.jpg',
    'whole-ogbono-seeds-5kg': 'whole_ogbono_seeds.jpg',
    'catfish-smoked-5kg': 'smoked_cat_fish.jpg',
    'crayfish-whole-5kg': 'crayfish_whole.jpg',
    'crayfish-ground-5kg': 'crayfish_ground.jpg',
    'snail-dried-frozen-5kg': 'dried_snail.jpg',
    'tigernut-milk-500ml': 'tigernut_milk.jpg',
    'coconut-milk-500ml': 'coconut_milk.jpg',
    'almond-milk-500ml': 'almond_milk.jpg',
    'soy-milk-500ml': 'soy_milk.jpg',
    'red-palm-oil-5l': 'red_palm_oil.jpg',
    'groundnut-oil-5l': 'groundnut_oil.jpg',
    'sunflower-oil-5l': 'sunflower_oil.jpg',
    'palm-olein-vegetable-oil-5l': 'vegetable_oil.jpg',
    'soybean-oil-5l': 'soybean_oil.jpg',
    'almond-oil-5l': 'almond_oil.jpg',
    'coconut-oil-5l': 'coconut_oil.jpg',
    'yam-flour-5kg': 'yam_flour.jpg',
    'cassava-flour-5kg': 'cassava_flour.jpg',
    'plantain-flour-5kg': 'plantain_flour.jpg',
    'cocoyam-flour-5kg': 'cocoyam_flour.jpg',
    'almond-flour-5kg': 'almond_flour.jpg',
    'soybean-flour-5kg': 'soybean_flour.jpg',
    'honey-bean-flour-5kg': 'honey_bean_flour.jpg',
    'garri-yellow-white-5kg': 'garri.jpg',
    'dry-red-pepper-chili-cameroon-pepper': 'dried_red_pepper.jpg',
    'ginger-powder-198g': 'ginger_powder.jpg',
    'garlic-powder-198g': 'garlic_powder.jpg',
    'turmeric-powder-198g': 'tumeric_powder.jpg',
    'dry-onion-powder-198g': 'dried_onion_powder.jpg',
    'red-pepper-paste-198g': 'red_pepper_paste.jpg',
    'tomato-paste-198g': 'tomato_paste.jpg',
    'tomato-ketchup-1kg': 'tomato_ketchup.jpg',
    'ginger-juice-500ml': 'ginger_juice.jpg',
    'zobo-hibiscus-drink-500ml': 'zobo.jpg',
    'turmeric-juice-500ml': 'tumeric_juice.jpg',
    'orange-juice-500ml': 'orange_juice.jpg',
    'pineapple-juice-500ml': 'pineapple_juice.jpg',
    'apple-juice-500ml': 'apple_juice.jpg',
    'mango-juice-500ml': 'mango_juice.jpg',
    'watermelon-juice-500ml': 'watermelon_juice.jpg',
    'table-water-500ml': 'table_water.jpg',
    'sachet-water-500ml': 'sachet_water.jpg',
    'fish-feed-15kg': 'fish_feed.jpg',
    'poultry-feed-25kg': 'poultry_feed.jpg',
}


def get_category_display_name(slug):
    return CATEGORY_DISPLAY_NAMES.get(slug, slug.replace('-', ' ').title())


def normalize_image_url(image_value):
    if not image_value:
        return ""

    value = str(image_value).strip().replace('\\', '/')

    if value.startswith(("http://", "https://", "data:")):
        return value

    if '/fakepath/' in value.lower() or re.match(r'^[A-Za-z]:/', value):
        value = value.rsplit('/', 1)[-1]

    if value.startswith("/static/") or value.startswith("/media/"):
        return value

    if value.startswith("static/") or value.startswith("media/"):
        return f"/{value}"

    if value.startswith("/gosh_main/images/"):
        return f"/static{value}"

    if value.startswith("gosh_main/images/"):
        return f"/static/{value}"

    if value.startswith("/"):
        return value

    if "/" not in value:
        return f"/static/gosh_main/images/{value}"

    return f"/static/{value}"


def resolve_product_image_url(product):
    raw_image = getattr(product, 'image', '')
    normalized = normalize_image_url(raw_image)

    image_name = (normalized.rsplit('/', 1)[-1].lower() if normalized else '')
    slug = str(getattr(product, 'slug', '') or '').strip().lower()

    if normalized and image_name not in GENERIC_CATEGORY_IMAGE_NAMES:
        return normalized

    fallback_filename = PRODUCT_SLUG_IMAGE_FALLBACKS.get(slug)
    if fallback_filename:
        return f"/static/gosh_main/images/{fallback_filename}"

    return normalized


def get_product_unit_label(product):
    if hasattr(product, 'get_unit_display'):
        try:
            display = product.get_unit_display()
            if display:
                return display
        except Exception:
            pass

    unit_value = str(getattr(product, 'unit', 'item') or 'item').strip().lower()
    return UNIT_LABELS.get(unit_value, 'item')


def is_customer_user(request):
    return request.user.is_authenticated and not request.user.is_superuser

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if not (username and password): # checks if any field is empty
            return render(request, "gosh_main/signin.html", {
                "message": "All fields are required.",
                "page": "login"
                })
        # Check if authentication successful
        if user is not None:
            # block anyone with superuser credentials without stating why
            if user.is_superuser:
                logger.warning(f"Blocked login attempt using superuser credentials from IP {request.META.get('REMOTE_ADDR')}")
                return render(request, "gosh_main/signin.html", {
                    "message": "Invalid username or password",
                    "page": "login"
                })
            login(request, user)
            print(f"Logged in as {user.username}")
            return HttpResponseRedirect(reverse("gosh_main:home"))
        else:
            existing_user = UserModel.objects.filter(username=username).first()
            if existing_user is None or not existing_user.is_active:
                return render(request, "gosh_main/signin.html", {
                    "message": "User Does not Exist",
                    "page": "login"
                })
            return render(request, "gosh_main/signin.html", {
                "message": "Invalid username and/or password.",
                "page": "login"
            })
    else:
        return render(request, "gosh_main/signin.html", {"page": "login"})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("gosh_main:home"))


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")

        # Ensure password matches confirmation
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")

        form_data = {
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }

        if not (username and email and first_name and last_name and password and confirmation):
            return render(request, "gosh_main/signup.html", {
                "message": "All fields are required.",
                "form_data": form_data,
                "page": "register"
            })

        if len(password) < 8:
            return render(request, "gosh_main/signup.html", {
                "message": "Password should be at least 8 characters.",
                "form_data": form_data,
                "page": "register"
            })

        if not password[0].isupper():
            return render(request, "gosh_main/signup.html", {
                "message": "Password must begin with an uppercase",
                "form_data": form_data,
                "page": "register"
            })

        if not re.search(r"\d", password):
            return render(request, "gosh_main/signup.html", {
                "message": "Password must have at least one number.",
                "formdata": form_data,
                "page": "register"
            })

        if not re.search(r"[^A-Za-z0-9]", password):
            return render(request, "gosh_main/signup.html", {
                "message": "Password must have at least one special character.",
                "form_data": form_data,
                "page": "register"
            })

        if password != confirmation:
            return render(request, "gosh_main/signup.html", {
                "message": "Passwords must match.",
                "form_data": form_data,
                "page": "register"
            })

        # Avoid accidentally recreating a superuser
        if UserModel.objects.filter(username=username, is_superuser=True).exists():
            return render(request, "gosh_main/signup.html", {
                "message": "Username already taken",
                "page": "register"
            })

        # Attempt to create new user
        try:
            user = UserModel.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            user.is_active = False
            user.save()
        except IntegrityError:
            return render(request, "gosh_main/signup.html", {
                "message": "Username already taken.",
                "page": "register"
            })

        token = email_verification_token.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = request.build_absolute_uri(
            reverse(
                "gosh_main:verify_email",
                kwargs={"uidb64": uidb64, "token": token},
            )
        )

        verification_message = render_to_string(
            "gosh_main/emails/email_verification.txt",
            {
                "user": user,
                "verification_url": verification_url,
                "expire_hours": 24,
            },
        )
        email_sent = send_email_verification_email(
            user.email,
            verification_message,
            "Verify your Goshen account",
        )

        if not email_sent:
            user.delete()
            return render(
                request,
                "gosh_main/signup.html",
                {
                    "message": "We could not send the verification email. Please check email settings and try again.",
                    "form_data": form_data,
                    "page": "register",
                },
            )

        return render(
            request,
            "gosh_main/email_verification_sent.html",
            {
                "page": "login",
                "email": user.email,
                "verification_url": verification_url if settings.DEBUG else None,
            },
        )
    else:
        return render(request, "gosh_main/signup.html", {"page": "register"})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if not user or not email_verification_token.check_token(user, token):
        return render(
            request,
            "gosh_main/email_verification_invalid.html",
            {"page": "login"},
        )

    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])

    return render(
        request,
        "gosh_main/signin.html",
        {
            "page": "login",
            "message": "Your email has been verified. You can sign in now.",
            "message_success": True,
        },
    )


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                reverse(
                    "gosh_main:password_reset_confirm",
                    kwargs={"uidb64": uidb64, "token": token},
                )
            )

            message = render_to_string(
                "gosh_main/emails/password_reset.txt",
                {
                    "user": user,
                    "reset_url": reset_url,
                    "expire_hours": 1,
                },
            )
            
            # Use SendGrid Web API helper (bypasses SMTP firewall issues)
            email_sent = send_password_reset_email(
                user.email,
                message,
                "Reset your Goshen password"
            )

            if not email_sent:
                return render(
                    request,
                    "gosh_main/password_reset_request.html",
                    {
                        "page": "login",
                        "form": form,
                        "message": "We could not send the password reset email. Please check email settings and try again.",
                    },
                )

            return render(
                request,
                "gosh_main/password_reset_sent.html",
                {
                    "page": "login",
                    "email": user.email,
                    "reset_url": reset_url if settings.DEBUG else None,
                },
            )
    else:
        form = PasswordResetRequestForm()

    return render(
        request,
        "gosh_main/password_reset_request.html",
        {"page": "login", "form": form},
    )


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if not user or not token_generator.check_token(user, token):
        return render(
            request,
            "gosh_main/password_reset_invalid.html",
            {"page": "login"},
        )

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password reset successful. You can sign in now.")
            return redirect("gosh_main:login")
    else:
        form = SetPasswordForm(user)

    return render(
        request,
        "gosh_main/password_reset_confirm.html",
        {"page": "login", "form": form},
    )

def home(request):
    """Render the home page with database-driven featured products."""
    featured = []

    try:
        top_selling_ids = list(
            OrderItem.objects.filter(order__payment_status='paid', product__isnull=False)
            .values('product')
            .annotate(total_purchased=Sum('quantity'))
            .order_by('-total_purchased', '-product')
            .values_list('product', flat=True)[:5]
        )

        if top_selling_ids:
            products_by_id = Product.objects.in_bulk(top_selling_ids)
            db_featured = [products_by_id[product_id] for product_id in top_selling_ids if product_id in products_by_id]
        else:
            db_featured = list(
                Product.objects
                .exclude(category__slug__in=EXCLUDED_CATEGORY_SLUGS)
                .filter(is_featured=True)
                .order_by('-created_at')[:6]
            )
            if not db_featured:
                db_featured = list(
                    Product.objects
                    .exclude(category__slug__in=EXCLUDED_CATEGORY_SLUGS)
                    .order_by('-created_at')[:6]
                )
    except Exception:
        db_featured = []

    db_featured = [
        product for product in db_featured
        if getattr(getattr(product, 'category', None), 'slug', '') not in EXCLUDED_CATEGORY_SLUGS
    ]

    if db_featured:
        for product in db_featured:
            product.image_url = resolve_product_image_url(product)
            featured.append(product)

    # Fetch random products for carousel (4-5 images)
    carousel_products = []
    try:
        all_products = Product.objects.exclude(category__slug__in=EXCLUDED_CATEGORY_SLUGS).all()
        if all_products.exists():
            num_carousel = min(5, all_products.count())
            random_products = random.sample(list(all_products), num_carousel)
            for product in random_products:
                product.image_url = resolve_product_image_url(product)
                carousel_products.append(product)
    except Exception:
        pass

    return render(
        request,
        "gosh_main/home.html",
        {
            "page": "home",
            "featured_products": featured,
            "carousel_products": carousel_products
        },
    )


def products(request):
    # Keep categories in sync with shop page
    try:
        db_cats = list(
            Category.objects
            .exclude(slug__in=EXCLUDED_CATEGORY_SLUGS)
            .order_by('name')
            .values('name', 'slug')
        )
        categories = db_cats if db_cats else []
    except Exception:
        categories = []

    return render(
        request,
        "gosh_main/products.html",
        {"page": "products", "categories": categories},
    )


from .models import AboutBlock, ContactInfo, ContactMessage, Product, Category, Review, NewsletterSignup, Address, Order, OrderItem, Payment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal




def about(request):
    return render(request, "gosh_main/about.html")
def shop(request):
    # Get category from URL parameter
    current_category = request.GET.get('cat', 'all')
    if current_category in EXCLUDED_CATEGORY_SLUGS:
        current_category = 'all'

    # Prefer DB products; fall back to mock list if DB is empty
    products = []
    try:
        if current_category and current_category != 'all':
            db_qs = (
                Product.objects
                .exclude(category__slug__in=EXCLUDED_CATEGORY_SLUGS)
                .filter(category__slug=current_category)
            )
        else:
            db_qs = (
                Product.objects
                .exclude(category__slug__in=EXCLUDED_CATEGORY_SLUGS)
            )
        products = list(db_qs.order_by('name'))
        for product in products:
            product.image_url = resolve_product_image_url(product)
    except Exception:
        products = []

    if not products:
        # If database is empty, return empty list instead of using mock data
        products = []
    
    
    # When you have a real database, use this instead:
    # if current_category and current_category != 'all':
    #     products = Product.objects.filter(category=current_category, is_active=True)
    # else:
    #     products = Product.objects.filter(is_active=True)
    
    # Pagination: 6 items per page
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 6)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Build categories list from database only
    try:
        categories = list(
            Category.objects
            .exclude(slug__in=EXCLUDED_CATEGORY_SLUGS)
            .order_by('name')
            .values('name', 'slug')
        )
    except Exception:
        categories = []

    current_category_name = 'All Products'
    if current_category and current_category != 'all':
        matched = next((category for category in categories if category.get('slug') == current_category), None)
        if matched:
            current_category_name = matched.get('name') or 'Products'

    context = {
        'page': 'shop',
        'products': products,
        'current_category': current_category,
        'current_category_name': current_category_name,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
    }
    
    return render(request, "gosh_main/shop.html", context)

def add_to_cart(request, product_id):
    """Add product to cart stored in session.

    Supports POST (from forms) and GET (used by simple links).
    Adds 1 (or `quantity` from POST) to the session cart for the product id.
    Redirects back to the referring page when available, otherwise to the shop.
    """
    # determine effective product id: prefer explicit POST product_id if provided
    effective_pid = None
    if request.method == 'POST':
        post_pid = request.POST.get('product_id')
        if post_pid:
            try:
                effective_pid = int(post_pid)
            except (TypeError, ValueError):
                effective_pid = None

    if effective_pid is None:
        try:
            effective_pid = int(product_id)
        except (TypeError, ValueError):
            messages.error(request, "Invalid product id")
            return redirect('gosh_main:shop')

    # get existing cart from session
    cart = request.session.get('cart', {})
    key = str(effective_pid)

    # determine quantity to add
    qty = 1
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty < 1:
                qty = 1
        except (TypeError, ValueError):
            qty = 1
    else:
        # for GET requests (e.g. simple +1 links) increment by 1
        qty = 1

    cart[key] = cart.get(key, 0) + qty
    request.session['cart'] = cart

    # Prefer to return to referring page so buttons on home/shop stay on the same page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('gosh_main:shop')

def product_detail(request, product_id):
    """Show product details"""
    # Prefer DB product; fallback to mock products
    try:
        pid_int = int(product_id)
    except (TypeError, ValueError):
        messages.error(request, "Invalid product id")
        return redirect('gosh_main:shop')

    try:
        product = Product.objects.get(id=pid_int)
        if getattr(getattr(product, 'category', None), 'slug', '') in EXCLUDED_CATEGORY_SLUGS:
            return redirect('gosh_main:shop')
        product.image_url = resolve_product_image_url(product)
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('gosh_main:shop')

    context = {
        'product': product,
        'page': 'shop',
        'product_unit_label': get_product_unit_label(product),
    }

    return render(request, "gosh_main/product_detail.html", context)

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
    return HttpResponseRedirect(reverse('gosh_main:cart'))

def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for pid, qty in cart.items():
        try:
            p = Product.objects.get(id=int(pid))
            p.image_url = resolve_product_image_url(p)
            items.append({ 'product': p, 'qty': qty, 'line_total': (p.price or 0) * qty })
            total += (p.price or 0) * qty
        except Product.DoesNotExist:
            # Skip products not in database instead of using mock data
            continue
    return render(request, "gosh_main/cart.html", {"page": "cart", "items": items, "total": total})

def checkout_address(request):
    # Address collection step. If logged in, allow saving.
    message = None
    if request.method == 'POST':
        data = {k: request.POST.get(k,'').strip() for k in ('label','recipient_name','phone','address_line','city','state','country')}
        save = request.POST.get('save_address') == 'on'
        # store in session as current_address
        request.session['checkout_address'] = data
        if is_customer_user(request) and save:
            Address.objects.create(user=request.user, **data)
        return HttpResponseRedirect(reverse('gosh_main:checkout_payment'))

    saved_addresses = []
    if is_customer_user(request):
        saved_addresses = list(request.user.addresses.all())
    return render(request, "gosh_main/checkout_address.html", {"page":"checkout","saved_addresses":saved_addresses})

def checkout_payment(request):
    """Handle payment method selection and initiate payment"""
    from .services.payment_service import payment_service
    from .services.stripe_gateway import StripeGateway
    from .services.paystack_gateway import PaystackGateway
    from .services.flutterwave_gateway import FlutterwaveGateway
    
    # Initialize payment gateways if not already registered
    if not payment_service.get_gateway('stripe'):
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', '') or 'test_key'
        stripe_webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        payment_service.register_gateway('stripe', StripeGateway(stripe_key, stripe_webhook_secret))
    
    if not payment_service.get_gateway('paystack'):
        paystack_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '') or 'test_key'
        paystack_public = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        payment_service.register_gateway('paystack', PaystackGateway(paystack_key, paystack_public))
    
    if not payment_service.get_gateway('flutterwave'):
        flutterwave_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', '') or 'test_key'
        flutterwave_public = getattr(settings, 'FLUTTERWAVE_PUBLIC_KEY', '')
        payment_service.register_gateway('flutterwave', FlutterwaveGateway(flutterwave_key, flutterwave_public))
    
    address_data = request.session.get('checkout_address')
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, "Your cart is empty")
        return redirect('gosh_main:cart')
    
    if request.method == 'POST':
        # Get selected payment method
        payment_method = request.POST.get('payment_method', 'stripe')
        
        print(f"========== CHECKOUT PAYMENT POST ==========")
        print(f"DEBUG: Payment method selected = '{payment_method}'")
        print(f"DEBUG: Cart contents = {cart}")
        print(f"DEBUG: User authenticated = {request.user.is_authenticated}")
        logger.info(f"Processing checkout payment with method: {payment_method}")
        
        # Create order
        try:
            # Calculate totals
            items = []
            subtotal = Decimal('0')
            
            for pid, qty in cart.items():
                try:
                    p = Product.objects.get(id=int(pid))
                    price = p.price or Decimal('0')
                    line_total = price * qty
                    items.append({
                        'product': p,
                        'product_name': p.name,
                        'product_price': price,
                        'qty': qty,
                        'line_total': line_total
                    })
                    subtotal += line_total
                except Product.DoesNotExist:
                    # Skip products not in database
                    continue
            
            print(f"DEBUG: Items processed = {len(items)}, subtotal = {subtotal}")
            
            if not items:
                print(f"DEBUG: NO ITEMS - redirecting to cart")
                messages.error(request, "No valid items in cart")
                return redirect('gosh_main:cart')
            
            # Calculate shipping (simple flat rate for now)
            shipping_cost = Decimal('1000')  # ₦1000 flat rate
            total = subtotal + shipping_cost
            
            print(f"DEBUG: Order total calculated = {total}")
            
            # Create order
            order = Order.objects.create(
                user=request.user if is_customer_user(request) else None,
                recipient_name=address_data.get('recipient_name', 'Customer') if address_data else 'Customer',
                phone=address_data.get('phone', '') if address_data else '',
                address_line=address_data.get('address_line', '') if address_data else '',
                city=address_data.get('city', '') if address_data else '',
                state=address_data.get('state', '') if address_data else '',
                country=address_data.get('country', 'Nigeria') if address_data else 'Nigeria',
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total=total,
                status='pending',
                payment_status='pending'
            )
            
            # Create order items
            for item_data in items:
                # For mock products, product will be a SimpleNamespace, set to None
                product_instance = item_data['product'] if hasattr(item_data['product'], '_state') else None
                
                OrderItem.objects.create(
                    order=order,
                    product=product_instance,
                    product_name=item_data['product_name'],
                    product_price=item_data['product_price'],
                    quantity=item_data['qty']
                )
            
            # Handle different payment methods
            if payment_method == 'stripe':
                # Use Stripe for credit/debit card payments
                try:
                    result = payment_service.create_payment('stripe', order, total, 'NGN')
                    
                    if result.get('success'):
                        # Create payment record
                        Payment.objects.create(
                            order=order,
                            payment_method='stripe',
                            amount=total,
                            status='pending',
                            gateway_reference=result.get('session_id'),
                            payer_email=request.user.email if is_customer_user(request) else '',
                            payer_name=order.recipient_name
                        )
                        
                        # Redirect to Stripe checkout
                        return redirect(result['checkout_url'])
                    else:
                        messages.error(request, f"Payment initialization failed: {result.get('error')}")
                        order.delete()
                        return redirect('gosh_main:checkout_payment')
                except Exception as e:
                    logger.error(f"Stripe payment error: {str(e)}")
                    messages.error(request, "Stripe is not configured. Please use another payment method.")
                    order.delete()
                    return redirect('gosh_main:checkout_payment')
            
            elif payment_method == 'paystack':
                # Use Paystack for local (Nigerian) payments
                try:
                    result = payment_service.create_payment('paystack', order, total, 'NGN')
                    
                    if result.get('success'):
                        # Create payment record
                        Payment.objects.create(
                            order=order,
                            payment_method='paystack',
                            amount=total,
                            status='pending',
                            gateway_reference=result.get('reference'),
                            payer_email=request.user.email if is_customer_user(request) else '',
                            payer_name=order.recipient_name
                        )
                        
                        # Redirect to Paystack checkout
                        return redirect(result['checkout_url'])
                    else:
                        messages.error(request, f"Payment initialization failed: {result.get('error')}")
                        order.delete()
                        return redirect('gosh_main:checkout_payment')
                except Exception as e:
                    logger.error(f"Paystack payment error: {str(e)}")
                    messages.error(request, "Paystack is not configured. Please use another payment method.")
                    order.delete()
                    return redirect('gosh_main:checkout_payment')
            
            elif payment_method == 'flutterwave':
                # Use Flutterwave for African payments (card, bank, USSD, etc.)
                try:
                    logger.info(f"Creating Flutterwave payment for order {order.order_number}, amount: {total}")
                    result = payment_service.create_payment('flutterwave', order, total, 'NGN')
                    logger.info(f"Flutterwave payment result: {result}")
                    print(f"DEBUG: Flutterwave result = {result}")  # Console debug
                    
                    if result.get('success'):
                        # Create payment record
                        # Flutterwave returns tx_ref, use it for both reference and transaction_id
                        tx_ref = result.get('tx_ref', '')
                        Payment.objects.create(
                            order=order,
                            payment_method='flutterwave',
                            amount=total,
                            status='pending',
                            gateway_reference=tx_ref,
                            gateway_transaction_id=tx_ref,  # Use tx_ref as transaction ID for now
                            payer_email=request.user.email if is_customer_user(request) else '',
                            payer_name=order.recipient_name
                        )
                        
                        # Redirect to Flutterwave checkout
                        checkout_url = result.get('checkout_url')
                        logger.info(f"Redirecting to Flutterwave: {checkout_url}")
                        print(f"DEBUG: Redirecting to {checkout_url}")  # Console debug
                        return redirect(checkout_url)
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        logger.error(f"Flutterwave payment init failed: {error_msg}")
                        print(f"DEBUG: Flutterwave FAILED - {error_msg}")  # Console debug
                        messages.error(request, f"Payment initialization failed: {error_msg}")
                        order.delete()
                        return redirect('gosh_main:checkout_payment')
                except Exception as e:
                    logger.error(f"Flutterwave payment exception: {str(e)}", exc_info=True)
                    print(f"DEBUG: Flutterwave EXCEPTION - {str(e)}")  # Console debug
                    messages.error(request, f"Flutterwave error: {str(e)}")
                    order.delete()
                    return redirect('gosh_main:checkout_payment')
            
            elif payment_method == 'bank_transfer':
                # Create payment record for bank transfer
                Payment.objects.create(
                    order=order,
                    payment_method='bank_transfer',
                    amount=total,
                    status='pending',
                    payer_email=request.user.email if is_customer_user(request) else '',
                    payer_name=order.recipient_name
                )
                
                # Clear cart
                request.session.pop('cart', None)
                request.session.pop('checkout_address', None)
                
                # Show bank transfer instructions
                context = {
                    'page': 'checkout',
                    'payment_method': 'bank_transfer',
                    'order': order,
                    'bank_details': {
                        'bank_name': 'First Bank',
                        'account_number': '0123456789',
                        'account_name': 'Goshen Giant Food'
                    }
                }
                return render(request, 'gosh_main/checkout_bank_transfer.html', context)
            
            else:
                messages.error(request, "Invalid payment method selected")
                order.delete()
                return redirect('gosh_main:checkout_payment')
                
        except Exception as e:
            logger.error(f"Order creation error: {str(e)}")
            messages.error(request, "An error occurred while processing your order")
            return redirect('gosh_main:checkout_payment')
    
    # GET request - show payment form
    # Build items summary
    items = []
    total = Decimal('0')
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(id=int(pid))
            price = p.price or Decimal('0')
            line_total = price * qty
            items.append({'product': p, 'qty': qty, 'line_total': line_total})
            total += line_total
        except Product.DoesNotExist:
            # Skip products not in database
            continue
    
    # All payment methods are available (will show configuration message if needed)
    return render(request, "gosh_main/checkout_payment.html", {
        "page": "checkout",
        "address": address_data,
        "items": items,
        "total": total,
    })



def contact(request):
    # retrieve contact information if set in admin
    contact_info = ContactInfo.objects.first()
    message_sent = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, subject=subject or '', message=message)
            message_sent = send_contact_email(name, email, subject, message)
            if not message_sent:
                messages.error(request, "We could not send your message right now. Please try again later.")
        else:
            messages.error(request, "Please fill in all required fields.")
    return render(request, "gosh_main/contact.html", {"page": "contact", "contact_info": contact_info, "message_sent": message_sent})


def newsletter_subscribe(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Method not allowed."}, status=405)

    email = (request.POST.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"ok": False, "message": "Email is required."}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"ok": False, "message": "Please enter a valid email address."}, status=400)

    signup, created = NewsletterSignup.objects.get_or_create(email=email)
    if created:
        return JsonResponse({"ok": True, "message": "Thanks for subscribing!"})

    return JsonResponse({"ok": True, "message": "You are already subscribed."})


def payment_success(request):
    """Handle successful payment callback"""
    from .services.payment_service import payment_service
    from .services.email_service import send_order_confirmation_email
    
    order_number = request.GET.get('order')
    session_id = request.GET.get('session_id')  # Stripe
    reference = request.GET.get('reference')  # Paystack
    transaction_id = request.GET.get('transaction_id')  # Flutterwave
    
    if not order_number:
        messages.error(request, "Invalid payment callback")
        return redirect('gosh_main:home')
    
    try:
        order = Order.objects.get(order_number=order_number)
        
        # Verify payment based on gateway
        payment = order.payments.first()
        if not payment:
            messages.error(request, "Payment record not found")
            return redirect('gosh_main:home')
        
        # Verify payment with gateway
        verified = False
        
        if payment.payment_method == 'stripe' and session_id:
            try:
                result = payment_service.verify_payment('stripe', session_id)
                if result.get('success') and result.get('status') in ['paid', 'complete']:
                    payment.status = 'completed'
                    payment.gateway_transaction_id = result.get('transaction_id')
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()
                    
                    verified = True
            except Exception as e:
                logger.error(f"Stripe verification error: {str(e)}")
        
        elif payment.payment_method == 'paystack':
            # Get reference from payment record if not in URL
            ref = reference or payment.gateway_reference
            if ref:
                try:
                    result = payment_service.verify_payment('paystack', ref)
                    if result.get('success') and result.get('status') == 'paid':
                        payment.status = 'completed'
                        payment.gateway_transaction_id = result.get('transaction_id')
                        payment.completed_at = timezone.now()
                        payment.save()
                        
                        order.payment_status = 'paid'
                        order.status = 'processing'
                        order.save()
                        
                        verified = True
                except Exception as e:
                    logger.error(f"Paystack verification error: {str(e)}")
        
        elif payment.payment_method == 'flutterwave':
            # Get transaction_id from URL or try to verify using reference
            tx_id = transaction_id
            if not tx_id:
                # Try to get from query params or payment record
                tx_id = request.GET.get('tx_ref') or payment.gateway_reference
            
            if tx_id:
                try:
                    result = payment_service.verify_payment('flutterwave', tx_id)
                    if result.get('success') and result.get('status') == 'paid':
                        payment.status = 'completed'
                        payment.gateway_transaction_id = result.get('transaction_id')
                        payment.completed_at = timezone.now()
                        payment.save()
                        
                        order.payment_status = 'paid'
                        order.status = 'processing'
                        order.save()
                        
                        verified = True
                except Exception as e:
                    logger.error(f"Flutterwave verification error: {str(e)}")
        
        # Clear cart on success
        if verified:
            request.session.pop('cart', None)
            request.session.pop('checkout_address', None)
            
            # Send confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {str(e)}")
            
            context = {
                'page': 'checkout',
                'order': order,
                'payment': payment,
                'verified': True
            }
            return render(request, 'gosh_main/checkout_success.html', context)
        else:
            messages.warning(request, "Payment verification pending. We'll send you an email when it's confirmed.")
            context = {
                'page': 'checkout',
                'order': order,
                'payment': payment,
                'verified': False
            }
            return render(request, 'gosh_main/checkout_success.html', context)
            
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect('gosh_main:home')


def payment_cancel(request):
    """Handle cancelled payment"""
    order_number = request.GET.get('order')
    
    if order_number:
        try:
            order = Order.objects.get(order_number=order_number)
            # Mark payment as cancelled
            payment = order.payments.first()
            if payment:
                payment.status = 'cancelled'
                payment.save()
            
            order.payment_status = 'failed'
            order.save()
            
            messages.warning(request, "Payment was cancelled. Your order has been saved and you can try again.")
            
            return render(request, 'gosh_main/payment_cancel.html', {
                'page': 'checkout',
                'order': order
            })
        except Order.DoesNotExist:
            pass
    
    messages.info(request, "Payment was cancelled")
    return redirect('gosh_main:cart')

def order_tracker(request):
    """Display the real-time order tracker page"""
    return render(request, "gosh_main/orders/order_list.html", {"page": "orders"})

def orders_api(request):
    """JSON API endpoint to return all orders"""
    orders = RestaurantOrder.objects.all().order_by('-created_at')
    
    orders_data = [
        {
            'id': order.id,
            'items': order.items,
            'status': order.status,
            'user': order.user.username if order.user else 'Guest',
            'created_at': order.created_at.isoformat()
        }
        for order in orders
    ]
    
    return JsonResponse({'orders': orders_data})

@login_required
def create_order_view(request):
    """Create a new restaurant order (for testing)"""
    if request.method == 'POST':
        items = request.POST.get('items', '{}')
        
        try:
            import json
            items_dict = json.loads(items)
        except json.JSONDecodeError:
            items_dict = {'note': items}
        
        order = RestaurantOrder.objects.create(
            user=request.user,
            items=items_dict,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': 'Order created successfully'
        })
    
    return render(request, "gosh_main/orders/create_order.html", {"page": "orders"})


# ============ ORDER TRACKING VIEWS ============

def track_order(request, tracking_number=None):
    """
    Display the order tracking page with map and real-time updates.
    Can be accessed via:
    - /track/?tracking_number=TRK-XXXXX
    - /track/{tracking_number}/
    """
    from .models import OrderTracking
    
    tracking = None
    error_message = None
    
    # Get tracking number from URL or query parameter
    if tracking_number:
        tracking = get_object_or_404(OrderTracking, tracking_number=tracking_number)
    elif request.method == 'POST' or request.GET.get('tracking_number'):
        tracking_number = request.POST.get('tracking_number') or request.GET.get('tracking_number')
        if tracking_number:
            tracking = OrderTracking.objects.filter(tracking_number=tracking_number).first()
            if not tracking:
                error_message = f"Tracking number '{tracking_number}' not found."
    
    context = {
        'page': 'tracking',
        'tracking': tracking,
        'mapbox_token': settings.MAPBOX_TOKEN if hasattr(settings, 'MAPBOX_TOKEN') else '',
        'error_message': error_message,
    }
    
    return render(request, 'gosh_main/tracking.html', context)


def my_orders_tracking(request):
    """
    Display tracking for all orders of the authenticated user.
    Requires login.
    """
    if not request.user.is_authenticated:
        return redirect('gosh_main:login')
    
    from .models import OrderTracking
    
    # Get all orders for this user
    user_orders = request.user.orders.all().order_by('-created_at')
    
    # Get tracking information for each order
    trackings = OrderTracking.objects.filter(order__user=request.user).select_related(
        'order', 'logistics_company'
    ).order_by('-created_at')
    
    context = {
        'page': 'tracking',
        'trackings': trackings,
        'mapbox_token': settings.MAPBOX_TOKEN if hasattr(settings, 'MAPBOX_TOKEN') else '',
        'total_orders': user_orders.count(),
        'delivered_orders': user_orders.filter(status='delivered').count(),
    }
    
    return render(request, 'gosh_main/my_orders_tracking.html', context)


def tracking_api(request, tracking_number):
    """
    API endpoint to get tracking information as JSON.
    Used by AJAX and WebSocket connections.
    """
    from .models import OrderTracking
    from decimal import Decimal
    
    tracking = get_object_or_404(OrderTracking, tracking_number=tracking_number)
    
    # Get tracking history
    history = tracking.history.all().order_by('-recorded_at')[:10]
    
    return JsonResponse({
        'success': True,
        'tracking': {
            'id': tracking.id,
            'tracking_number': tracking.tracking_number,
            'order_id': tracking.order.id,
            'order_number': tracking.order.order_number,
            'status': tracking.status,
            'status_display': tracking.get_status_display(),
            'current_location': {
                'lat': float(tracking.current_location_lat),
                'lng': float(tracking.current_location_lng),
                'name': tracking.current_location_name,
            },
            'destination_location': {
                'lat': float(tracking.destination_lat),
                'lng': float(tracking.destination_lng),
            },
            'logistics_company': {
                'name': tracking.logistics_company.name,
                'phone': tracking.logistics_company.phone,
                'logo': tracking.logistics_company.logo,
            } if tracking.logistics_company else None,
            'estimated_delivery': tracking.estimated_delivery.isoformat() if tracking.estimated_delivery else None,
            'delivered_at': tracking.delivered_at.isoformat() if tracking.delivered_at else None,
            'is_delivered': tracking.is_delivered,
            'created_at': tracking.created_at.isoformat(),
            'updated_at': tracking.updated_at.isoformat(),
        },
        'history': [
            {
                'location_name': h.location_name,
                'location_lat': float(h.location_lat),
                'location_lng': float(h.location_lng),
                'status_display': h.get_status_display(),
                'message': h.message,
                'recorded_at': h.recorded_at.isoformat(),
            }
            for h in history
        ]
    })


def update_tracking_location(request):
    """
    Admin endpoint to update a package's location.
    Used by delivery personnel or admin panel.
    Requires specific permissions.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from .models import OrderTracking
    from .services.logistics_service import LogisticsService, broadcast_tracking_update
    
    try:
        import json
        data = json.loads(request.body)
        
        tracking_id = data.get('tracking_id')
        lat = data.get('latitude')
        lng = data.get('longitude')
        location_name = data.get('location_name')
        status = data.get('status')
        message = data.get('message', '')
        
        tracking = get_object_or_404(OrderTracking, id=tracking_id)
        
        # Update the location
        history = LogisticsService.update_location(
            tracking=tracking,
            latitude=lat,
            longitude=lng,
            location_name=location_name,
            status=status,
            message=message
        )
        
        # Broadcast the update via WebSocket
        broadcast_tracking_update(tracking)
        
        return JsonResponse({
            'success': True,
            'message': 'Location updated successfully',
            'tracking': {
                'status': tracking.status,
                'current_location_lat': float(tracking.current_location_lat),
                'current_location_lng': float(tracking.current_location_lng),
                'current_location_name': tracking.current_location_name,
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def search_tracking(request):
    """
    Search functionality for tracking numbers.
    Returns JSON with matching tracking records.
    """
    from .models import OrderTracking
    
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 3:
        return JsonResponse({
            'results': [],
            'message': 'Enter at least 3 characters'
        })
    
    # Search by tracking number or order number
    trackings = OrderTracking.objects.filter(
        tracking_number__icontains=query
    ) | OrderTracking.objects.filter(
        order__order_number__icontains=query
    )
    
    results = [
        {
            'tracking_number': t.tracking_number,
            'order_number': t.order.order_number,
            'status': t.get_status_display(),
            'url': f'/track/{t.tracking_number}/',
        }
        for t in trackings[:10]
    ]
    
    return JsonResponse({
        'results': results,
        'count': len(results),
    })
