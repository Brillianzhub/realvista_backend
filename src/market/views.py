from rest_framework import status, permissions
from .serializers import MarketPropertyListSerializer
from django.conf import settings
from rest_framework.permissions import AllowAny
from accounts.models import User
from .serializers import MarketPropertyFileSerializer
from django.db.models import F
from .serializers import MarketCoordinateListSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.forms import ValidationError
from rest_framework.pagination import PageNumberPagination
from .serializers import PropertyImageUploadSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.decorators import api_view
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import MarketProperty, BookmarkedProperty, PropertyImage, MarketFeatures, MarketPropertyFile, MarketCoordinate
from .serializers import MarketPropertySerializer, PropertyImageUploadSerializer


@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated])
def upload_property(request):
    user = request.user
    property_data = request.data.copy()
    property_id = property_data.get('property_id')

    if request.method == 'PUT' and not property_id:
        return Response(
            {"detail": "Property ID is required for updates."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if property_id:
            # Fetch the property for updating
            property_instance = MarketProperty.objects.get(
                id=property_id, owner=user)
            serializer = MarketPropertySerializer(
                property_instance, data=property_data, partial=True
            )
            action = "updated"
        else:
            # Create a new property
            property_data['owner'] = user.id
            serializer = MarketPropertySerializer(data=property_data)
            action = "created"

        if serializer.is_valid():
            serializer.save(owner=user)
            return Response(
                {
                    "detail": f"Property successfully {action}.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK if action == "updated" else status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except MarketProperty.DoesNotExist:
        return Response(
            {"detail": "Property not found or you don't have permission to update it."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": "An unexpected error occurred.", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@permission_classes([AllowAny])
def fetch_listed_light_properties(request):
    try:
        city = request.query_params.get('city')
        state = request.query_params.get('state')
        description = request.query_params.get('description')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        general_search = request.query_params.get('general_search')

        properties = MarketProperty.objects.prefetch_related('images').all()

        if city:
            properties = properties.filter(city__iexact=city)
        if state:
            properties = properties.filter(state__icontains=state)
        if description:
            properties = properties.filter(description__icontains=description)
        if min_price and max_price:
            properties = properties.filter(
                price__gte=min_price, price__lte=max_price)
        elif min_price:
            properties = properties.filter(price__gte=min_price)
        elif max_price:
            properties = properties.filter(price__lte=max_price)

        if general_search:
            properties = properties.filter(
                Q(city__icontains=general_search)
                | Q(state__icontains=general_search)
                | Q(description__icontains=general_search)
                | Q(address__icontains=general_search)
                | Q(title__icontains=general_search)
            )

        paginator = StandardResultsPagination()
        paginated_properties = paginator.paginate_queryset(properties, request)

        serializer = MarketPropertyListSerializer(
            paginated_properties, many=True)
        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response(
            {
                "error": "An error occurred while fetching properties",
                "details": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def fetch_listed_properties(request):
    try:
        city = request.query_params.get('city')
        state = request.query_params.get('state')
        description = request.query_params.get('description')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        general_search = request.query_params.get('general_search')

        properties = MarketProperty.objects.all()

        if city:
            properties = properties.filter(city__iexact=city)
        if state:
            properties = properties.filter(state__icontains=state)
        if description:
            properties = properties.filter(description__icontains=description)
        if min_price and max_price:
            properties = properties.filter(
                price__gte=min_price, price__lte=max_price)
        elif min_price:
            properties = properties.filter(price__gte=min_price)
        elif max_price:
            properties = properties.filter(price__lte=max_price)

        if general_search:
            properties = properties.filter(
                Q(city__icontains=general_search) |
                Q(state__icontains=general_search) |
                Q(description__icontains=general_search) |
                Q(address__icontains=general_search) |
                Q(title__icontains=general_search)
            )

        paginator = StandardResultsPagination()
        paginated_properties = paginator.paginate_queryset(properties, request)

        serializer = MarketPropertySerializer(paginated_properties, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response(
            {
                "error": "An error occurred while fetching properties",
                "details": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def fetch_property_by_id(request, property_id):
    try:
        property = MarketProperty.objects.get(id=property_id)

        serializer = MarketPropertySerializer(property)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except MarketProperty.DoesNotExist:
        return Response(
            {
                "error": "Property not found",
                "details": f"No property found with ID {property_id}"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {
                "error": "An error occurred while fetching the property",
                "details": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_user_listed_properties(request):
    try:
        properties = MarketProperty.objects.filter(owner=request.user)

        serializer = MarketPropertySerializer(properties, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "An error occured while fetching properties",
             "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_properties_by_email(request):
    email = request.query_params.get('email')

    if not email:
        return Response(
            {"error": "Email parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        owner = User.objects.filter(email=email).first()

        if not owner:
            return Response(
                {"error": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        properties = MarketProperty.objects.filter(
            owner=owner).order_by('-listed_date')[:20]
        serializer = MarketPropertySerializer(properties, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "An error occurred while fetching properties",
                "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def search_properties(request):
    title = request.query_params.get('title', None)
    location = request.query_params.get(
        'location', None)
    min_price = request.query_params.get('min_price', None)
    max_price = request.query_params.get('max_price', None)

    filters = Q()
    if title:
        filters &= Q(title__icontains=title)
    if location:
        filters &= Q(city__icontains=location) | Q(state__icontains=location)
    if min_price:
        try:
            filters &= Q(price__gte=float(min_price))
        except ValueError:
            return Response({"error": "Invalid min_price value"}, status=HTTP_400_BAD_REQUEST)
    if max_price:
        try:
            filters &= Q(price__lte=float(max_price))
        except ValueError:
            return Response({"error": "Invalid max_price value"}, status=HTTP_400_BAD_REQUEST)

    properties = MarketProperty.objects.filter(filters)
    serializer = MarketPropertyListSerializer(properties, many=True)

    return Response(serializer.data, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def view_property(request, pk):
    try:
        property_obj = MarketProperty.objects.get(pk=pk)

        # Increment view count
        property_obj.views = (property_obj.views or 0) + 1
        property_obj.save()

        serializer = MarketPropertySerializer(property_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except MarketProperty.DoesNotExist:
        return Response(
            {"error": "Property not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": "An error occurred while fetching the property",
                "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_bookmark(request, bookmark_id):
    try:
        bookmark = BookmarkedProperty.objects.filter(
            id=bookmark_id, user=request.user).first()

        if not bookmark:
            return Response(
                {"message": "Bookmark does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )

        property_obj = bookmark.property
        property_obj.bookmarked = max((property_obj.bookmarked or 0) - 1, 0)
        property_obj.save()

        bookmark.delete()

        return Response(
            {"message": "Bookmark removed successfully"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": "An error occurred while removing the bookmark",
             "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request, pk):
    try:
        property_obj = MarketProperty.objects.get(pk=pk)
        user = request.user

        bookmark, created = BookmarkedProperty.objects.get_or_create(
            user=user, property=property_obj
        )

        if not created:
            bookmark.delete()
            MarketProperty.objects.filter(pk=pk).update(
                bookmarked=F('bookmarked') - 1
            )
            message = "Bookmark removed successfully"
        else:
            MarketProperty.objects.filter(pk=pk).update(
                bookmarked=F('bookmarked') + 1
            )
            message = "Property bookmarked successfully"

        return Response(
            {"message": message},
            status=status.HTTP_200_OK
        )

    except MarketProperty.DoesNotExist:
        return Response(
            {"error": "Property not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": "An error occurred while toggling the bookmark",
             "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inquire_property(request, pk):
    try:
        property_obj = MarketProperty.objects.get(pk=pk)

        property_obj.inquiries = (property_obj.inquiries or 0) + 1
        property_obj.save()

        return Response(
            {"message": "Inquiry initiated successfully"},
            status=status.HTTP_200_OK
        )

    except MarketProperty.DoesNotExist:
        return Response(
            {"error": "Property not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": "An error occurred while initiating the inquiry",
             "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_property(request, pk):
    try:
        property_obj = MarketProperty.objects.get(pk=pk)

        property_obj.delete()

        return Response(
            {"message": "Property deleted successfully"},
            status=status.HTTP_200_OK
        )

    except MarketProperty.DoesNotExist:
        return Response(
            {"error": "Property not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": "An error occurred while deleting the property",
             "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_bookmarks(request):
    user = request.user
    bookmarks = BookmarkedProperty.objects.filter(
        user=user
    ).select_related('property').prefetch_related('property__market_property_files')

    data = []
    for bookmark in bookmarks:
        property = bookmark.property
        # Filter only image files (optional logic can be adjusted)
        images = MarketPropertyFile.objects.filter(
            property=property
        ).filter(
            file__iregex=r'\.(jpg|jpeg|png|gif|bmp)$'
        )

        image_urls = [
            file.file.url if file.file else file.image_url
            for file in images
            if file.file or file.image_url
        ]

        data.append({
            "bookmark_id": bookmark.id,
            "property_id": property.id,
            "title": property.title,
            "property_type": property.property_type,
            "listing_purpose": property.listing_purpose,
            "address": property.address,
            "city": property.city,
            "state": property.state,
            "currency": property.currency,
            "price": property.price,
            "bookmarked_at": bookmark.created_at,
            "images": image_urls,
        })

    return Response(data, status=status.HTTP_200_OK)


class PropertyImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'error': 'Property ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = MarketProperty.objects.get(id=property_id)
        except MarketProperty.DoesNotExist:
            return Response({'error': 'Invalid property ID'}, status=status.HTTP_404_NOT_FOUND)

        saved_images = []

        image_urls = request.data.get('image_url', [])
        for image_url in image_urls:
            property_image = PropertyImage(
                property=property_instance, image_url=image_url)
            try:
                property_image.clean()
                property_image.save()
                saved_images.append(
                    PropertyImageUploadSerializer(property_image).data)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if 'image' in request.FILES:
            images = request.FILES.getlist('image')
            for image in images:
                property_image = PropertyImage(
                    property=property_instance, image=image)
                try:
                    property_image.clean()
                    property_image.save()
                    saved_images.append(
                        PropertyImageUploadSerializer(property_image).data)
                except ValidationError as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not saved_images:
            return Response({'error': 'No valid images or URLs provided'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'status': 'Images uploaded successfully', 'data': saved_images},
            status=status.HTTP_201_CREATED
        )


class MarketPropertyFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'error': 'Property ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = MarketProperty.objects.get(id=property_id)
        except MarketProperty.DoesNotExist:
            return Response({'error': 'Invalid property ID'}, status=status.HTTP_404_NOT_FOUND)

        if 'file' not in request.FILES:
            return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('file')
        saved_files = []

        for file in files:
            file_name = file.name

            property_file = MarketPropertyFile(
                property=property_instance,
                file=file,
                name=file_name
            )
            property_file.save()

            saved_files.append(
                MarketPropertyFileSerializer(property_file).data)

        return Response(
            {'status': 'Files uploaded successfully', 'data': saved_files},
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_market_features(request, property_id):
    try:
        property = MarketProperty.objects.get(id=property_id)

        negotiable = request.data.get('negotiable', 'no')
        furnished = request.data.get('furnished', False)
        pet_friendly = request.data.get('pet_friendly', False)
        parking_available = request.data.get('parking_available', False)
        swimming_pool = request.data.get('swimming_pool', False)
        garden = request.data.get('garden', False)
        electricity_proximity = request.data.get('electricity_proximity', None)
        road_network = request.data.get('road_network', None)
        development_level = request.data.get('development_level', None)
        water_supply = request.data.get('water_supply', False)
        security = request.data.get('security', False)

        market_features, created = MarketFeatures.objects.update_or_create(
            market_property=property,
            defaults={
                'negotiable': negotiable,
                'furnished': furnished,
                'pet_friendly': pet_friendly,
                'parking_available': parking_available,
                'swimming_pool': swimming_pool,
                'garden': garden,
                'electricity_proximity': electricity_proximity,
                'road_network': road_network,
                'development_level': development_level,
                'water_supply': water_supply,
                'security': security
            }
        )

        message = "Market Features created successfully" if created else "Market Features updated successfully"

        return Response(
            {"message": message, "features_id": market_features.id},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    except MarketProperty.DoesNotExist:
        return Response(
            {"error": "Market property not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": "An error occurred", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CoordinateBulkCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MarketCoordinateListSerializer(data=request.data)
        if serializer.is_valid():
            created_coordinates = serializer.save()  # will always be a list with 1 item
            return Response(
                {
                    "message": f"{len(created_coordinates)} coordinate saved successfully!",
                    "data": [
                        {
                            "id": coord.id,
                            "property": coord.property.id,
                            "latitude": coord.latitude,
                            "longitude": coord.longitude
                        } for coord in created_coordinates
                    ]
                },
                status=status.HTTP_201_CREATED
            )

        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class CoordinateBulkCreateAPIView(APIView):
#     def post(self, request, *args, **kwargs):

#         serializer = MarketCoordinateListSerializer(data=request.data)
#         if serializer.is_valid():
#             created_coordinates = serializer.save()
#             return Response(
#                 {
#                     "message": f"{len(created_coordinates)} coordinates saved successfully!",
#                     "data": [
#                         {
#                             "id": coord.id,
#                             "property": coord.property.id,
#                             "latitude": coord.latitude,
#                             "longitude": coord.longitude
#                         }
#                         for coord in created_coordinates
#                     ]
#                 },
#                 status=status.HTTP_201_CREATED
#             )

#         print("Validation errors:", serializer.errors)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PropertyWithFilesUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        files = request.FILES.getlist('file')

        property_id = data.get('property_id')

        # Validate and Save Property
        try:
            if property_id:
                property_instance = MarketProperty.objects.get(
                    id=property_id, owner=user)
                serializer = MarketPropertySerializer(
                    property_instance, data=data, partial=True)
                action = "updated"
            else:
                data['owner'] = user.id
                serializer = MarketPropertySerializer(data=data)
                action = "created"

            if serializer.is_valid():
                property_instance = serializer.save(owner=user)

                # Optional File Uploads
                uploaded_files = []
                for file in files:
                    property_file = MarketPropertyFile(
                        property=property_instance,
                        file=file,
                        name=file.name
                    )
                    property_file.save()
                    uploaded_files.append(
                        MarketPropertyFileSerializer(property_file).data)

                return Response({
                    "detail": f"Property successfully {action}.",
                    "property": serializer.data,
                    "uploaded_files": uploaded_files
                }, status=status.HTTP_200_OK if action == "updated" else status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except MarketProperty.DoesNotExist:
            return Response({"detail": "Property not found or you don't have permission to update it."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": "An unexpected error occurred.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoordinateDeleteAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        coord_id = request.data.get("id")

        if not coord_id:
            return Response(
                {"error": "Coordinate ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            coord = MarketCoordinate.objects.get(id=coord_id)
            coord.delete()
            return Response(
                {"message": f"Coordinate with ID {coord_id} deleted successfully."},
                status=status.HTTP_200_OK
            )
        except MarketCoordinate.DoesNotExist:
            return Response(
                {"error": f"Coordinate with ID {coord_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )


class PropertyFileDeleteAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        file_id = request.data.get("id")

        if not file_id:
            return Response(
                {"error": "File ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            file_instance = MarketPropertyFile.objects.get(id=file_id)

            if file_instance.file:
                file_instance.file.delete(save=False)

            file_instance.delete()
            return Response(
                {"message": f"File with ID {file_id} deleted successfully."},
                status=status.HTTP_200_OK
            )

        except MarketPropertyFile.DoesNotExist:
            return Response(
                {"error": f"File with ID {file_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_market_property_file(request, pk):
    """
    DELETE /market/delete-file/<int:pk>/
    Deletes a file from a MarketPropertyFile entry and S3 if applicable.
    """
    try:
        file_instance = MarketPropertyFile.objects.get(pk=pk)
    except MarketPropertyFile.DoesNotExist:
        return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

    # Optional: check ownership
    # if file_instance.property.vendor != request.user:
    #     return Response({"error": "You do not have permission to delete this file."},
    #                     status=status.HTTP_403_FORBIDDEN)

    # Delete from S3 if applicable
    # if file_instance.file:
    #     try:
    #         storage = file_instance.file.storage
    #         if storage.exists(file_instance.file.name):
    #             storage.delete(file_instance.file.name)
    #     except Exception as e:
    #         print("Error deleting from storage:", e)

    file_instance.delete()
    return Response({"message": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
