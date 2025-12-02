from .models import MarketPropertyFile
from .models import MarketFeatures
from .models import BookmarkedProperty
from django.contrib import admin
from .models import MarketProperty, PropertyImage, MarketCoordinate


admin.site.register(MarketCoordinate)


@admin.register(BookmarkedProperty)
class BookmarkedPropertyAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    search_fields = ('user__user', 'property__title')
    list_filter = ('created_at',)


class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'uploaded_at')
    search_fields = ('property__name',)
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)


admin.site.register(PropertyImage, PropertyImageAdmin)


@admin.register(MarketFeatures)
class MarketFeaturesAdmin(admin.ModelAdmin):
    list_display = (
        'market_property',
        'negotiable',
        'furnished',
        'pet_friendly',
        'parking_available',
        'electricity_proximity',
        'road_network',
        'development_level',
        'water_supply',
        'security',
        'verified_user',
    )
    list_filter = (
        'negotiable',
        'furnished',
        'pet_friendly',
        'parking_available',
        'electricity_proximity',
        'road_network',
        'development_level',
        'verified_user',
    )
    search_fields = ('market_property__title',)


@admin.register(MarketProperty)
class MarketPropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'property_type',
        'price',
        'currency',
        'listing_purpose',
        'city',
        'state',
        'availability',
    )
    list_filter = (
        'property_type',
        'listing_purpose',
        'availability',
        'city',
        'state',
    )
    search_fields = ('title', 'owner__email', 'city', 'state')


@admin.register(MarketPropertyFile)
class MarketPropertyFileAdmin(admin.ModelAdmin):
    list_display = ('property', 'name', 'file', 'file_type', 'uploaded_at')
    search_fields = ('property__title', 'name', 'file')
    list_filter = ('uploaded_at',)

    def file_type(self, obj):
        return obj.file_type()
    file_type.short_description = "File Type"
