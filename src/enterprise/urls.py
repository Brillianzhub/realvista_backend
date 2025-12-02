from django.urls import path
from . import views

urlpatterns = [
    path('create-group/', views.create_group, name='create-group'),
    path('update-group/<int:group_id>/',
         views.update_group, name='update-group'),
    path('delete-group/<int:group_id>/',
         views.delete_group, name='delete-group'),

    path('groups/<int:group_id>/members/',
         views.fetch_group_members, name='fetch_group_members'),
    path('groups/<int:pk>/add-member/',
         views.invite_member, name='invite_member'),
    path('groups/join/', views.join_group, name='join_group'),

    path('groups/<uuid:group_id>/properties/',
         views.fetch_group_properties, name='fetch_group_properties'),

    path('groups/<uuid:group_id>/properties/create/',
         views.create_or_update_group_property, name='create_group_property'),
    path('groups/<uuid:group_id>/<int:property_id>/update/',
         views.create_or_update_group_property),

    path('groups/<uuid:group_id>/properties/<int:property_id>/',
         views.delete_group_property, name='delete_group_property'),

    path('upload-group-image/', views.GroupPropertyImageUploadView.as_view(),
         name='upload-group-image'),
    path('groups/<int:property_id>/book-slot/',
         views.book_slot, name='book_slot'),
    path('property/bookings/<int:property_id>/',
         views.fetch_all_bookings, name='fetch_all_bookings'),
    path('bookings/<int:booking_id>/confirm-payment/',
         views.confirm_payment, name='confirm_payment'),

    path('bookings/<int:booking_id>/make-payment/',
         views.make_payment, name='make_payment'),

    path('property/add-income/', views.add_property_income,
         name='add_property_income'),
    path('property/add-expense/', views.add_property_expense,
         name='add_property_expense'),

    path('members/<int:group_id>/make-admin/',
         views.MakeAdminView.as_view(), name='make-admin'),
    path('members/<int:group_id>/remove-admin/',
         views.RemoveAdminView.as_view(), name='remove-admin'),
    path('members/<int:group_id>/remove-user/',
         views.RemoveUserView.as_view(), name='remove-user'),

    path('upload-file-group/', views.GroupPropertyFileUploadView.as_view(),
         name='upload-file-group'),
    path('delete-file/<int:file_id>/',
         views.GroupPropertyFileDeleteView.as_view(), name='delete-file'),

    path('group-property/coordinates/', views.CoordinateBulkCreateAPIView.as_view(),
         name='group-property-coordinate'),
    path("group-property/coordinate/<int:coordinate_id>/delete/",
         views.delete_coordinate, name="delete-coordinate"),

    path('cancel-booking/<int:booking_id>/',
         views.cancel_slot_booking, name='cancel-slot-booking'),
    path("transfer-slots/", views.transfer_slots_view, name="transfer_slots"),

    path('released-slots/', views.get_released_slots, name='get_released_slots'),
    path('release-slot/', views.release_slots, name='release_slots'),
    path('get-slots-total/', views.get_total_released_slots_for_authenticated_user, name='get_slots_total')
]
