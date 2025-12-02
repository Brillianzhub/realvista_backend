from .serializers import AgentVerificationSerializer
from .models import AgentVerification
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, permissions
from .serializers import AgentRatingSerializer
from .models import AgentRating
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Agent
from .serializers import AgentSerializer, AgentRatingSerializer, AgentStatSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_agents(request):
    agents = Agent.objects.filter(verified=True)
    serializer = AgentSerializer(agents, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_stat_by_id(request, agent_id):
    try:
        agent = Agent.objects.get(id=agent_id)
        serializer = AgentStatSerializer(agent)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Agent.DoesNotExist:
        return Response({'detail': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_by_id(request, agent_id):
    try:
        agent = Agent.objects.get(id=agent_id)
        serializer = AgentSerializer(agent)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Agent.DoesNotExist:
        return Response({'detail': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)


class RateAgentView(generics.CreateAPIView):
    queryset = AgentRating.objects.all()
    serializer_class = AgentRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        agent_id = request.data.get('agent')

        if not agent_id:
            return Response({'error': 'Agent ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a rating by this user already exists for the agent
        existing_rating = AgentRating.objects.filter(
            user=user, agent_id=agent_id).first()

        if existing_rating:
            serializer = self.get_serializer(
                existing_rating, data=request.data, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_200_OK if existing_rating else status.HTTP_201_CREATED)

class AgentVerificationViewSet(viewsets.ModelViewSet):
    queryset = AgentVerification.objects.all()
    serializer_class = AgentVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        agent = getattr(self.request.user, 'agent_profile', None)
        if not agent:
            raise ValidationError("Only agents can submit verification.")

        # If verification exists, update it
        verification = getattr(agent, 'verification', None)
        if verification:
            # Update existing instance
            serializer.instance = verification  # Attach to serializer
            serializer.save(agent=agent)
        else:
            # Create new
            serializer.save(agent=agent)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AgentVerification.objects.all()
        return AgentVerification.objects.filter(agent=user.agent_profile)

# class AgentVerificationViewSet(viewsets.ModelViewSet):
#     queryset = AgentVerification.objects.all()
#     serializer_class = AgentVerificationSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         agent = getattr(self.request.user, 'agent_profile', None)
#         if not agent:
#             raise ValidationError("Only agents can submit verification.")
#         if hasattr(agent, 'verification'):
#             raise ValidationError("Verification already submitted.")
#         serializer.save(agent=agent)

#     def get_queryset(self):
#         # Agents see only their own verification record
#         user = self.request.user
#         if user.is_staff:
#             return AgentVerification.objects.all()
#         return AgentVerification.objects.filter(agent=user.agent_profile)
