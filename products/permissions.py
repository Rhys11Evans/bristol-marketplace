from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.producer == request.user


class IsProducerForWriteOrReadOnly(BasePermission):
    """
    Allows anyone to read products.
    Only authenticated producers can create/update/delete products.
    """

    message = "Only producers can create or edit products."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_producer", False)
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_producer", False)
            and obj.producer == request.user
        )