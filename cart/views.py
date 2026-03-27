from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer
from products.models import Product

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartSerializer


class CartView(APIView):
    """
    GET /api/cart/
    S2-T2: Protected — requires authentication (JWT or session).
    S2-T3: Only CUSTOMER role can access. Producer gets 403.
    """
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    """
    POST /api/cart/add/
    S2-T2: Protected — requires authentication.
    S2-T3: Only CUSTOMER role can add items to cart.
    """
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        # Check product exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Add or update quantity
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(
            {
                'message': f'Added {quantity}x {product.name} to cart.',
                'cart': CartSerializer(cart).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RemoveFromCartView(APIView):
    """
    DELETE /api/cart/remove/<item_id>/
    S2-T2: Protected — requires authentication.
    S2-T3: Only CUSTOMER role can remove items.
    """
    permission_classes = [IsAuthenticated, IsCustomer]

    def delete(self, request, item_id):
        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(id=item_id, cart=cart)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response(
                {'error': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        product_name = item.product.name
        item.delete()
        return Response(
            {
                'message': f'Removed {product_name} from cart.',
                'cart': CartSerializer(cart).data,
            }
        )
