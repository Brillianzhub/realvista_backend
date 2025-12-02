from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_default_category():
        """Ensure 'Real Estate' exists and return its ID"""
        category, created = Category.objects.get_or_create(name="Real Estate")
        return category.id


class Report(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Detailed content of the report")
    slug = models.SlugField(blank=True, unique=True)
    source = models.CharField(
        max_length=255, help_text="Name of the source of the report"
    )
    url = models.URLField(blank=True, null=True,
                          help_text="External link for more details")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    attachment = models.FileField(upload_to='reports/', blank=True, null=True)
    views = models.PositiveIntegerField(
        default=0, help_text="Number of times this report has been viewed"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="reports",
        default=Category.get_default_category
    )
    publish = models.BooleanField(
        default=False, help_text="Whether the report is published or not"
    )

    def increment_views(self):
        """Increase view count by 1."""
        self.views += 1
        self.save(update_fields=['views'])

    def save(self, *args, **kwargs):
        """Automatically create a unique slug from title before saving."""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Report.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
