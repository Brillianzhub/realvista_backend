from django.urls import path
from . import views
from .views import RateAgentView, AgentVerificationViewSet

verification_list = AgentVerificationViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

verification_detail = AgentVerificationViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('', views.get_all_agents, name='get_all_agents'),
    path('<int:agent_id>/', views.get_agent_by_id, name='get_agent_by_id'),
    path('stat/<int:agent_id>/', views.get_agent_stat_by_id,
         name='get_agent_stat_by_id'),
    path('rate-agent/', RateAgentView.as_view(), name='rate-agent'),

    # New verification endpoints
    path('verifications/', verification_list, name='agent-verification-list'),
    path('verifications/<int:pk>/', verification_detail,
         name='agent-verification-detail'),
]
