import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Safely extracts client IP address from the request."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def record_audit_log(actor, action_type, target, reason="", previous_state=None, new_state=None, request=None):
    """
    Creates an append-only audit log record for an administrative action.

    Args:
        actor (User): The administrator performing the action.
        action_type (str): Value from AuditLog.ActionType.
        target: The target model instance or representation.
        reason (str): Justification provided by administrator.
        previous_state (dict, optional): Previous serialized state.
        new_state (dict, optional): New serialized state.
        request (HttpRequest, optional): Active request for IP logging.

    Returns:
        AuditLog: The created audit log instance, or None on failure.
    """
    try:
        target_model = target._meta.model_name.capitalize() if hasattr(target, '_meta') else str(type(target).__name__)
        target_object_id = str(target.pk) if hasattr(target, 'pk') else ""
        target_repr = str(target)[:250] if target else ""

        ip_address = get_client_ip(request)

        log = AuditLog.objects.create(
            actor=actor if (actor and actor.is_authenticated) else None,
            action_type=action_type,
            target_model=target_model,
            target_object_id=target_object_id,
            target_repr=target_repr,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason or "",
            ip_address=ip_address,
        )
        return log
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}", exc_info=True)
        return None
