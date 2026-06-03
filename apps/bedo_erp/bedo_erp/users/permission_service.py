from bedo_erp.security.policies import require_active_bedo_profile


def enforce_protected_endpoint_access(user=None):
    require_active_bedo_profile(user)
