from django.db import models
from django.utils.text import slugify
import re


class Learn(models.Model):
    CATEGORY_CHOICES = [
        ('Real Estate', 'Real Estate'),
        ('Finance', 'Finance'),
        ('Investment', 'Investment'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    youtube_url = models.URLField()
    youtube_id = models.CharField(
        max_length=50, blank=True, null=True, editable=False)
    thumbnail_url = models.URLField(blank=True, null=True, editable=False)
    duration = models.CharField(max_length=20, blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Learn Resource"
        verbose_name_plural = "Learn Resources"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug if missing
        if not self.slug:
            self.slug = slugify(self.title)

        # Extract YouTube video ID
        if self.youtube_url:
            video_id = self.extract_youtube_id()
            if video_id:
                self.youtube_id = video_id
                self.thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        super().save(*args, **kwargs)

    def extract_youtube_id(self):
        """
        Extracts the YouTube video ID from various URL formats.
        Supports:
        - https://www.youtube.com/watch?v=XXXX
        - https://youtu.be/XXXX
        - https://www.youtube.com/embed/XXXX
        """
        pattern = r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})"
        match = re.search(pattern, self.youtube_url)
        return match.group(1) if match else None
