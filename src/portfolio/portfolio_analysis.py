from collections import defaultdict
from decimal import Decimal


def analyze_portfolio_summary(user, rates, preferred_currency='USD'):
    from .serializers import PortfolioSummarySerializer

    personal_properties = user.properties.filter(
        owner=user, group_property_id__isnull=True)
    group_properties = user.properties.filter(
        owner=user, group_property_id__isnull=False)

    all_properties = personal_properties | group_properties

    context = {'currency': preferred_currency, 'rates': rates}

    def calculate_summary(properties):
        serializer = PortfolioSummarySerializer(
            instance=properties, many=True, context=context)
        data = serializer.data
        total_initial_cost = sum(item['total_initial_cost'] for item in data)
        total_current_value = sum(item['total_current_value'] for item in data)
        total_income = sum(item['total_income'] for item in data)
        total_expenses = sum(item['total_expenses'] for item in data)
        net_cash_flow = total_income - total_expenses
        total_appreciation = total_current_value - total_initial_cost
        average_appreciation = total_appreciation / \
            len(data) if data else Decimal(0)
        average_percentage_performance = (
            (total_appreciation / total_initial_cost) * 100
            if total_initial_cost > 0
            else Decimal(0)
        )

        return {
            "total_initial_cost": round(total_initial_cost, 2),
            "total_current_value": round(total_current_value, 2),
            "total_appreciation": round(total_appreciation, 2),
            "average_appreciation": round(average_appreciation, 2),
            "average_percentage_performance": round(average_percentage_performance, 2),
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_cash_flow": round(net_cash_flow, 2),
        }

    # Generate summaries
    personal_summary = calculate_summary(personal_properties)
    group_summary = calculate_summary(group_properties)
    overall_summary = calculate_summary(all_properties)

    return {
        "personal_summary": personal_summary,
        "group_summary": group_summary,
        "overall_summary": overall_summary,
    }
