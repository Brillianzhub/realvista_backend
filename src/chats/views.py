from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from enterprise.models import CorporateEntity
from rest_framework.generics import ListAPIView

import logging

logger = logging.getLogger(__name__)


class ChatMessageView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            group = CorporateEntity.objects.get(group_id=data.get('groupID'))
            data['group'] = group.id

            serializer = ChatMessageSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CorporateEntity.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


logger = logging.getLogger(__name__)


class GroupChatMessagesView(ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get('uniqueGroupID')
        if not group_id:
            logger.warning("No group_id provided in query params.")
            return ChatMessage.objects.none()

        queryset = ChatMessage.objects.filter(
            group__group_id=group_id).order_by('timestamp')

        # Log only essential information
        if queryset.exists():
            logger.info(
                f"Retrieved {queryset.count()} messages for group_id: {group_id[:4]}***")
        else:
            logger.warning(
                f"No messages found for group_id: {group_id[:4]}***")

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            logger.warning("No messages found for the provided group_id.")
            return Response({"error": "No messages found for this group."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
