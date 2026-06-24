from __future__ import annotations


def execute() -> None:
    """Ensure existing sites have the current ARD roles and seed assignments."""
    from bedo_platform.setup import seed_dashboards, seed_departments, seed_initial_users, seed_roles

    seed_departments.execute()
    seed_roles.execute()
    seed_dashboards.execute()
    seed_initial_users.execute(strict=False)
