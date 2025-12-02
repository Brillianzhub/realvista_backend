from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import CategorySerializer
from .models import Category
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from rest_framework.decorators import action
from rest_framework import status
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes


class ReportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.filter(publish=True).order_by('-date_created')
    serializer_class = ReportSerializer
    pagination_class = ReportPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'body', 'slug', 'category__name']
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    @action(detail=True, methods=['patch'], url_path='update-views')
    def update_views(self, request, slug=None):
        report = self.get_object()
        report.views += 1
        report.save(update_fields=['views'])
        return Response({'views': report.views}, status=status.HTTP_200_OK)


def get_all_reports(request):
    reports = Report.objects.all().order_by('-date_created')
    serializer = ReportSerializer(reports, many=True)
    return JsonResponse(serializer.data, safe=False)


@api_view(['POST'])
@permission_classes([AllowAny])
def increment_report_views(request, slug):
    """
    Increment the view count for a specific report by slug.
    """
    try:
        report = Report.objects.get(slug=slug)
        report.increment_views()
        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Report.DoesNotExist:
        return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_or_update_report(request, pk=None):
    if request.method == 'POST':
        # Create new report
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT/PATCH - update existing report
    report = get_object_or_404(Report, pk=pk)
    serializer = ReportSerializer(
        report,
        data=request.data,
        partial=(request.method == 'PUT')
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST', 'PUT', 'PATCH'])
# @permission_classes([IsAuthenticated])
# @parser_classes([MultiPartParser, FormParser])
# def create_or_update_report(request):
#     if request.method == 'POST':
#         # --- CREATE ---
#         serializer = ReportSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     else:
#         # --- UPDATE ---
#         report_id = request.data.get('id') or request.query_params.get('id')
#         if not report_id:
#             return Response(
#                 {"detail": "Report ID is required for updates."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         report = get_object_or_404(Report, id=report_id)

#         serializer = ReportSerializer(
#             report,
#             data=request.data,
#             partial=(request.method == 'PATCH')  # PATCH = partial update
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class TrendCreateUpdateView(APIView):
#     permission_classes = [AllowAny]
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request):
#         serializer = ReportSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request, pk=None):
#         if not pk:
#             return Response({"detail": "Report ID (pk) is required for update."}, status=400)
#         report = get_object_or_404(Report, pk=pk)
#         serializer = ReportSerializer(report, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def patch(self, request, pk=None):
#         if not pk:
#             return Response({"detail": "Report ID (pk) is required for partial update."}, status=400)
#         report = get_object_or_404(Report, pk=pk)
#         serializer = ReportSerializer(report, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all().order_by('name')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TogglePublishView(APIView):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report.publish = not report.publish
        report.save(update_fields=['publish'])
        return Response({'publish': report.publish}, status=status.HTTP_200_OK)


class ReportListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        reports = Report.objects.all().order_by('-date_created')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
