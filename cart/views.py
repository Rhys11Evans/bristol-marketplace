from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, ExpressionWrapper, DecimalField
from decimal import Decimal

from products.models import Product, Category
from products.services import reduce_product_stock

from .models import Cart, CartItem, Order, OrderItem
from .forms import AddToCartForm, CreateCartForm, UpdateQuantityForm

User = get_user_model()


def check_customer(request):
    # only customers and admin can access shop pages
    if not (request.user.is_customer or request.user.is_staff):
        messages.error(request, "Only customers can access this page.")
        return redirect("cart:producer_order_list")
    return None


def check_producer(request):
    # only producers and admin can access producer pages
    if not (request.user.is_producer or request.user.is_staff):
        messages.error(request, "Only producers can access this page.")
        return redirect("cart:product_list")
    return None


def logout_view(request):
    logout(request)
    return redirect("login")


# home redirect based on role
@login_required
def home(request):
    if hasattr(request.user, 'is_producer') and request.user.is_producer:
        return redirect("cart:producer_order_list")
    return redirect("cart:product_list")


# -------------------------- Product listing -----------------------------
@login_required
def product_list(request):
    blocked = check_customer(request)
    if blocked:
        return blocked

    products = Product.objects.filter(is_available=True)

    # search
    search_query = request.GET.get("search", "").strip()
    if search_query:
        products = products.filter(name__icontains=search_query)

    # filter by category
    category_id = request.GET.get("category", "")
    if category_id:
        products = products.filter(category_id=category_id)

    # filter by producer
    producer_id = request.GET.get("producer", "")
    if producer_id:
        products = products.filter(producer_id=producer_id)

    # sorting
    products = products.order_by("category__name", "name")

    # pagination
    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    # carts
    user_carts = Cart.objects.filter(user=request.user)
    if not user_carts.exists():
        Cart.objects.create(user=request.user, name="My Cart")
        user_carts = Cart.objects.filter(user=request.user)

    selected_cart_id = request.GET.get("cart", user_carts.first().pk)

    # filter options for dropdowns
    categories = Category.objects.order_by("name")
    producers = User.objects.filter(products__isnull=False).distinct().order_by("username")

    return render(request, "cart/product_list.html", {
        "page_obj": page_obj,
        "carts": user_carts,
        "selected_cart_id": int(selected_cart_id),
        "search_query": search_query,
        "categories": categories,
        "selected_category": category_id,
        "producers": producers,
        "selected_producer": producer_id,
    })


@login_required
def add_to_cart(request):
    blocked = check_customer(request)
    if blocked:
        return blocked

    if request.method != "POST":
        return redirect("cart:product_list")

    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))
    cart_id = request.POST.get("cart_id")

    product = get_object_or_404(Product, pk=product_id, is_available=True)
    cart = get_object_or_404(Cart, pk=cart_id, user=request.user)

    if quantity > product.stock_quantity:
        messages.error(request, f"Only {product.stock_quantity} of {product.name} in stock.")
        return redirect(request.META.get("HTTP_REFERER", "cart:product_list"))

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, f"Added {quantity}x {product.name} to {cart.name}.")
    return redirect(request.META.get("HTTP_REFERER", "cart:product_list"))


# ---------------------------- Cart management -------------------------------
@login_required
def cart_list(request):
    blocked = check_customer(request)
    if blocked:
        return blocked

    carts = Cart.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "cart/cart_list.html", {"carts": carts})


@login_required
def create_cart(request):
    blocked = check_customer(request)
    if blocked:
        return blocked

    if request.method == "POST":
        form = CreateCartForm(request.POST)
        if form.is_valid():
            cart = form.save(commit=False)
            cart.user = request.user
            cart.save()
            messages.success(request, f"Cart '{cart.name}' created.")
    return redirect("cart:cart_list")


@login_required
def delete_cart(request, cart_id):
    blocked = check_customer(request)
    if blocked:
        return blocked

    if request.method == "POST":
        cart = get_object_or_404(Cart, pk=cart_id, user=request.user)
        name = cart.name
        cart.delete()
        messages.success(request, f"Cart '{name}' deleted.")
    return redirect("cart:cart_list")


CART_SORT_FIELDS = {
    "name": "product__name",
    "category": "product__category__name",
    "producer": "product__producer__username",
    "unit_price": "product__price",
    "quantity": "quantity",
    "total_price": "computed_total",
}


@login_required
def cart_detail(request, cart_id):
    blocked = check_customer(request)
    if blocked:
        return blocked

    cart = get_object_or_404(Cart, pk=cart_id, user=request.user)
    items = (
        cart.items
        .select_related("product", "product__category", "product__producer")
        .annotate(
            computed_total=ExpressionWrapper(
                F("product__price") * F("quantity"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
    )

    # sorting
    sort_by = request.GET.get("sort", "category")
    sort_dir = request.GET.get("dir", "asc")
    secondary = request.GET.get("secondary", "name")
    secondary_dir = request.GET.get("sdir", "asc")

    primary_field = CART_SORT_FIELDS.get(sort_by, "product__category__name")
    secondary_field = CART_SORT_FIELDS.get(secondary, "product__name")

    if sort_dir == "desc":
        primary_field = f"-{primary_field}"
    if secondary_dir == "desc":
        secondary_field = f"-{secondary_field}"

    if CART_SORT_FIELDS.get(sort_by) == CART_SORT_FIELDS.get(secondary):
        items = items.order_by(primary_field)
    else:
        items = items.order_by(primary_field, secondary_field)

    # pagination
    paginator = Paginator(items, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    # commission calc
    subtotal = cart.total
    commission = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    total = subtotal + commission

    return render(request, "cart/cart_detail.html", {
        "cart": cart,
        "page_obj": page_obj,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "secondary": secondary,
        "secondary_dir": secondary_dir,
        "subtotal": subtotal,
        "commission": commission,
        "total": total,
    })


@login_required
def update_cart_item(request, item_id):
    blocked = check_customer(request)
    if blocked:
        return blocked

    if request.method != "POST":
        return redirect("cart:cart_list")

    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    new_qty = int(request.POST.get("quantity", 1))

    if new_qty < 1:
        messages.error(request, "Quantity must be at least 1.")
    elif new_qty > item.product.stock_quantity:
        messages.error(request, f"Only {item.product.stock_quantity} of {item.product.name} in stock.")
    else:
        item.quantity = new_qty
        item.save()
        messages.success(request, f"Updated {item.product.name} to {new_qty}.")

    return redirect("cart:cart_detail", cart_id=item.cart.pk)


@login_required
def remove_cart_item(request, item_id):
    blocked = check_customer(request)
    if blocked:
        return blocked

    if request.method != "POST":
        return redirect("cart:cart_list")

    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart_id = item.cart.pk
    name = item.product.name
    item.delete()
    messages.success(request, f"Removed {name} from cart.")
    return redirect("cart:cart_detail", cart_id=cart_id)


# ------------------------------ Checkout ----------------------------------
@login_required
def checkout(request, cart_id):
    blocked = check_customer(request)
    if blocked:
        return blocked

    if request.method != "POST":
        return redirect("cart:cart_detail", cart_id=cart_id)

    cart = get_object_or_404(Cart, pk=cart_id, user=request.user)

    if cart.is_empty:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart_detail", cart_id=cart_id)

    # create order from cart
    order = Order.objects.create(user=request.user)

    for cart_item in cart.items.select_related("product").all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            item_price=cart_item.product.price,
        )
        # reduce stock (uses Rhys's service)
        reduce_product_stock(cart_item.product, cart_item.quantity)

    # calculate totals
    order.calculate_totals()

    # clear the cart
    cart.items.all().delete()

    messages.success(request, f"Order #{order.pk} placed successfully!")
    return redirect("cart:order_confirmation", order_id=order.pk)


# ------------------------- Customer Order Views ----------------------------
ORDER_SORT_FIELDS = {
    "name": "product__name",
    "category": "product__category__name",
    "producer": "product__producer__username",
    "unit_price": "item_price",
    "quantity": "quantity",
    "total_price": "computed_total",
}


@login_required
def order_confirmation(request, order_id):
    blocked = check_customer(request)
    if blocked:
        return blocked

    order = get_object_or_404(Order, pk=order_id, user=request.user)
    items = (
        order.order_items
        .select_related("product", "product__category", "product__producer")
        .annotate(
            computed_total=ExpressionWrapper(
                F("item_price") * F("quantity"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
    )

    # sorting
    sort_by = request.GET.get("sort", "category")
    sort_dir = request.GET.get("dir", "asc")
    secondary = request.GET.get("secondary", "name")
    secondary_dir = request.GET.get("sdir", "asc")

    primary_field = ORDER_SORT_FIELDS.get(sort_by, "product__category__name")
    secondary_field = ORDER_SORT_FIELDS.get(secondary, "product__name")

    if sort_dir == "desc":
        primary_field = f"-{primary_field}"
    if secondary_dir == "desc":
        secondary_field = f"-{secondary_field}"

    if ORDER_SORT_FIELDS.get(sort_by) == ORDER_SORT_FIELDS.get(secondary):
        items = items.order_by(primary_field)
    else:
        items = items.order_by(primary_field, secondary_field)

    # pagination
    paginator = Paginator(items, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    # commission for display
    food_total = order.total_price
    commission = order.commission
    total = food_total + commission

    return render(request, "cart/order_confirmation.html", {
        "order": order,
        "page_obj": page_obj,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "secondary": secondary,
        "secondary_dir": secondary_dir,
        "food_total": food_total,
        "commission": commission,
        "total": total,
    })


@login_required
def order_list(request):
    blocked = check_customer(request)
    if blocked:
        return blocked

    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "cart/order_list.html", {"orders": orders})


# ------------------------- Producer Order Views ----------------------------

NEXT_STATUS = {
    "pending": "confirmed",
    "confirmed": "ready",
    "ready": "delivered",
}


@login_required
def producer_order_list(request):
    blocked = check_producer(request)
    if blocked:
        return blocked

    # only show orders that contain this producer's products
    orders = (
        Order.objects
        .filter(order_items__product__producer=request.user)
        .distinct()
        .order_by("-created_at")
    )

    return render(request, "cart/producer_order_list.html", {"orders": orders})


@login_required
def producer_order_detail(request, order_id):
    blocked = check_producer(request)
    if blocked:
        return blocked

    order = get_object_or_404(Order, pk=order_id)

    # only show items belonging to this producer
    items = (
        order.order_items
        .filter(product__producer=request.user)
        .select_related("product", "product__category")
        .order_by("product__category__name", "product__name")
    )

    if not items.exists():
        messages.error(request, "This order has no items from you.")
        return redirect("cart:producer_order_list")

    return render(request, "cart/producer_order_detail.html", {
        "order": order,
        "items": items,
    })


@login_required
def update_item_status(request, item_id):
    if request.method != "POST":
        return redirect("cart:producer_order_list")

    item = get_object_or_404(OrderItem, pk=item_id)
    if item.product.producer != request.user and not request.user.is_staff:
        messages.error(request, "You can only update your own items.")
        return redirect("cart:producer_order_list")

    next_status = NEXT_STATUS.get(item.status)
    if next_status is None:
        messages.error(request, f"{item.product.name} is already delivered.")
    else:
        item.status = next_status
        item.save(update_fields=["status"])
        messages.success(request, f"{item.product.name} updated to {item.get_status_display()}.")

    return redirect("cart:producer_order_detail", order_id=item.order.pk)