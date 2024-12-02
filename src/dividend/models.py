from django.db import models
from accounts.models import User
from projects.models import Project


class Dividend(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='dividends')
    month = models.DateField(null=True, blank=True)
    total_return = models.DecimalField(
        max_digits=12, decimal_places=2)
    total_expenses = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.month.strftime('%B, %Y')}"

    def calculate_user_shares(self):

        net_return = self.total_return - self.total_expenses
        if net_return < 0:
            raise ValueError("Net return cannot be negative.")

        orders = self.project.orders.all()
        total_slots = sum(order.quantity for order in orders)

        if total_slots == 0:
            return []

        user_shares = []
        retention_percentage = 1.50

        for order in orders:
            user_share = (order.quantity / total_slots) * net_return
            final_share = user_share * \
                (1 - (float(retention_percentage) / 100))

            user_shares.append({
                "user": order.user,
                "share": user_share,
                "final_share": final_share,
                "retention_percentage": retention_percentage
            })

            DividendShare.objects.create(
                dividend=self,
                user=order.user,
                share_amount=user_share,
                retention_percentage=retention_percentage,
                final_share_amount=final_share,
                net_return=net_return,
                total_slots=total_slots
            )

        return user_shares


class DividendShare(models.Model):
    dividend = models.ForeignKey(
        Dividend, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='dividend_shares')
    share_amount = models.DecimalField(max_digits=12, decimal_places=2)
    retention_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.00)
    final_share_amount = models.DecimalField(
        max_digits=12, decimal_places=2)
    net_return = models.DecimalField(max_digits=12, decimal_places=2)
    total_slots = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.final_share_amount = self.share_amount * \
            (1 - (self.retention_percentage / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email
