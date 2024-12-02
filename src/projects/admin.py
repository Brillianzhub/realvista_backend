from django.contrib import admin
from .models import Project, ProjectImage


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'location', 'type_of_project', 'budget', 'cost_per_slot', 'num_slots', 'ordered_slots', 'total_cost'
    )
    list_filter = ('type_of_project', 'location')  # Optional filters


admin.site.register(ProjectImage)
