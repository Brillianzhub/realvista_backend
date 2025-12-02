# models.py (or utils file)
from django.db.models import Sum
from datetime import datetime
from django.utils.timezone import localtime


def get_performance_data(property_instance):
    """
    Returns performance data dynamically:
    - If history < 12 months, use month names (Jan, Feb...)
    - Else, use years
    """
    history = property_instance.value_history.order_by(
        "recorded_at")  # ✅ fixed line

    if not history.exists():
        return None

    # Extract timestamps and values
    dates = [localtime(h.recorded_at) for h in history]
    values = [float(h.value) / 1_000_000 for h in history]  # scale to millions

    # Detect if less than a year span
    start_year = dates[0].year
    end_year = dates[-1].year
    year_span = end_year - start_year

    if year_span == 0:  # less than 1 year
        labels = [d.strftime("%b")
                  for d in dates]  # e.g. ['Jan', 'Feb', 'Mar']
    else:
        # ['2023', '2024', '2025']
        labels = sorted(list(set(str(d.year) for d in dates)))

    return {
        "labels": labels,
        "datasets": [
            {"data": values}
        ],
        "unit": "Million"
    }


def get_portfolio_performance(user):
    """
    Calculate the overall portfolio performance for a given user.
    Returns a dictionary with total initial value, total current value,
    appreciation, and percentage performance.
    """
    from .models import Property

    # Fetch all properties belonging to this user
    properties = Property.objects.filter(owner=user)

    if not properties.exists():
        return {
            "total_initial_value": 0,
            "total_current_value": 0,
            "total_appreciation": 0,
            "portfolio_performance": 0,
        }

    # Aggregate totals using Django ORM
    totals = properties.aggregate(
        total_initial_value=Sum('initial_cost'),
        total_current_value=Sum('current_value')
    )

    total_initial = totals['total_initial_value'] or 0
    total_current = totals['total_current_value'] or 0
    total_appreciation = total_current - total_initial

    # Avoid division by zero
    portfolio_performance = (
        (total_appreciation / total_initial) * 100 if total_initial > 0 else 0
    )

    return {
        "total_initial_value": total_initial,
        "total_current_value": total_current,
        "total_appreciation": total_appreciation,
        "portfolio_performance": round(portfolio_performance, 2),
    }
