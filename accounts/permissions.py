from rest_framework.permissions import BasePermission


class IsProducer(BasePermission):
    """
    S1-T3: Only users with role=PRODUCER can access.
    Returns 403 for customers.
    """
    message = 'Only producers can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_producer
        )


class IsCustomer(BasePermission):
    """
    Only users with role=CUSTOMER can access.
    Returns 403 for producers.
    """
    message = 'Only customers can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_customer
        )
