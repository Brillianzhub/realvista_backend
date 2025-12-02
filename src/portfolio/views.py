from .utils import get_portfolio_performance
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .serializers import PortfolioPropertyFileSerializer
from .models import Property, PortfolioPropertyFile
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import CoordinateListSerializer
from .models import CurrencyRate
from .serializers import PortfolioSummarySerializer
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializers import PropertySerializer, IncomeSerializer, ExpensesSerializer, PortfolioPropertyImageUploadSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Income, Property, Expenses, PortfolioPropertyImage, Coordinate


@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated])
def add_or_update_property(request):
    user = request.user
    property_data = request.data.copy()

    property_id = property_data.get('property_id')

    if property_id:
        try:
            property_instance = Property.objects.get(
                id=property_id, owner=user)
        except Property.DoesNotExist:
            return Response(
                {"detail": "Property not found or you don't have permission to update it."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PropertySerializer(
            property_instance, data=property_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    else:
        property_data['owner'] = user.id
        serializer = PropertySerializer(data=property_data)
        if serializer.is_valid():
            serializer.save(owner=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_income(request):
    user = request.user
    data = request.data.copy()

    try:
        property = Property.objects.get(id=data.get('property'), owner=user)
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found or you don't have access to this property."},
            status=status.HTTP_404_NOT_FOUND,
        )

    data['user'] = user.id

    serializer = IncomeSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=user, property=property)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddIncomeView(CreateAPIView):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddExpenseView(CreateAPIView):
    queryset = Expenses.objects.all()
    serializer_class = ExpensesSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_expenses(request):
    user = request.user
    data = request.data.copy()

    try:
        property = Property.objects.get(id=data.get('property_id'), owner=user)
    except Property.DoesNotExist:
        return Response({"error": "Property not found or you don't have access to this property."}, status=status.HTTP_404_NOT_FOUND)

    data['property'] = property.id

    serializer = ExpensesSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_property(request, property_id):
    try:
        property = Property.objects.get(id=property_id, owner=request.user)
        property.delete()
        return Response({"message": "Property deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    except Property.DoesNotExist:
        return Response({"error": "Property not found or you don't have access to this property."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_properties(request):
    try:
        user = request.user

        properties = Property.objects.filter(
            owner=user).prefetch_related('incomes', 'expenses')

        serializer = PropertySerializer(properties, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:

        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PortfolioAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_rates_from_model(self):
        rates = CurrencyRate.objects.all()
        return {rate.currency_code: rate.rate for rate in rates}

    def get(self, request, *args, **kwargs):
        user = request.user
        rates = self.get_rates_from_model()
        preferred_currency = request.GET.get('currency', 'USD')

        personal_properties = user.properties.filter(
            owner=user, group_property_id__isnull=True)
        group_properties = user.properties.filter(
            owner=user, group_property_id__isnull=False)

        personal_summary_serializer = PortfolioSummarySerializer(
            instance=personal_properties,
            context={'currency': preferred_currency, 'rates': rates}
        )
        personal_summary = personal_summary_serializer.data

        group_summary_serializer = PortfolioSummarySerializer(
            instance=group_properties,
            context={'currency': preferred_currency, 'rates': rates}
        )
        group_summary = group_summary_serializer.data

        overall_properties = personal_properties | group_properties
        overall_summary_serializer = PortfolioSummarySerializer(
            instance=overall_properties,
            context={'currency': preferred_currency, 'rates': rates}
        )
        overall_summary = overall_summary_serializer.data

        return Response({
            "personal_summary": personal_summary,
            "group_summary": group_summary,
            "overall_summary": overall_summary,
        })


class CoordinateBulkCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):

        serializer = CoordinateListSerializer(data=request.data)
        if serializer.is_valid():
            created_coordinates = serializer.save()
            return Response(
                {
                    "message": f"{len(created_coordinates)} coordinates saved successfully!",
                    "data": [
                        {
                            "id": coord.id,
                            "property": coord.property.id,
                            "latitude": coord.latitude,
                            "longitude": coord.longitude
                        }
                        for coord in created_coordinates
                    ]
                },
                status=status.HTTP_201_CREATED
            )

        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PortfolioPropertyImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'error': 'Property ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return Response({'error': 'Invalid property ID'}, status=status.HTTP_404_NOT_FOUND)

        if 'image' not in request.FILES:
            return Response({'error': 'No image files provided'}, status=status.HTTP_400_BAD_REQUEST)

        images = request.FILES.getlist('image')

        saved_images = []
        for image in images:
            property_image = PortfolioPropertyImage(
                property=property_instance, image=image)
            property_image.save()
            saved_images.append(
                PortfolioPropertyImageUploadSerializer(property_image).data)

        return Response(
            {'status': 'Images uploaded successfully', 'data': saved_images},
            status=status.HTTP_201_CREATED
        )


class PortfolioPropertyFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'error': 'Property ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return Response({'error': 'Invalid property ID'}, status=status.HTTP_404_NOT_FOUND)

        if 'file' not in request.FILES:
            return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('file')
        saved_files = []

        for file in files:
            file_name = file.name

            property_file = PortfolioPropertyFile(
                property=property_instance,
                file=file,
                name=file_name
            )
            property_file.save()

            saved_files.append(
                PortfolioPropertyFileSerializer(property_file).data)

        return Response(
            {'status': 'Files uploaded successfully', 'data': saved_files},
            status=status.HTTP_201_CREATED
        )


class PropertyFileDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id, *args, **kwargs):
        try:
            file_instance = PortfolioPropertyFile.objects.get(id=file_id)
        except PortfolioPropertyFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        file_instance.delete()
        return Response({'status': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@csrf_exempt
def delete_coordinate(request, coordinate_id):
    if request.method == "DELETE":
        coordinate = get_object_or_404(Coordinate, id=coordinate_id)
        coordinate.delete()
        return JsonResponse({"message": "Coordinate deleted successfully"}, status=200)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_portfolio_summary(request):
    data = get_portfolio_performance(request.user)
    return Response(data)
