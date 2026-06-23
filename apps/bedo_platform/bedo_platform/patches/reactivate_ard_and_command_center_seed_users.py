from __future__ import annotations


def execute() -> None:
    """Repair ARD and Command Center seed data without resetting passwords."""
    from bedo_platform.setup import seed_departments, seed_initial_users, seed_roles

    seed_departments.execute()
    seed_roles.execute()
    seed_initial_users.execute(strict=False)
