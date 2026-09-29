from .models import Claim
from items.models import Item


def claims_context(request):
    """
    Supplies claims badge counts and report ownership flags for navigation.
    """
    if request.user.is_authenticated:
        has_found_reports = Item.objects.filter(
            user=request.user,
            item_type=Item.ItemType.FOUND
        ).exists()
        pending_review_count = Claim.objects.filter(
            item__user=request.user,
            status=Claim.Status.PENDING
        ).count()
        user_pending_claims_count = Claim.objects.filter(
            claimant=request.user,
            status=Claim.Status.PENDING
        ).count()
        return {
            'has_found_reports': has_found_reports,
            'pending_review_count': pending_review_count,
            'user_pending_claims_count': user_pending_claims_count,
        }
    return {
        'has_found_reports': False,
        'pending_review_count': 0,
        'user_pending_claims_count': 0,
    }
