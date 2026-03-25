from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Members
    path('members/', views.member_list, name='member_list'),
    path('members/new/', views.member_create, name='member_create'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/deactivate/', views.member_deactivate, name='member_deactivate'),

    # Sacraments overview
    path('sacraments/', views.sacrament_list, name='sacrament_list'),

    # Baptism
    path('members/<int:member_pk>/baptism/add/', views.baptism_create, name='baptism_create'),
    path('baptism/<int:pk>/edit/', views.baptism_edit, name='baptism_edit'),
    path('baptism/<int:pk>/print/', views.baptism_print, name='baptism_print'),

    # Confirmation
    path('members/<int:member_pk>/confirmation/add/', views.confirmation_create, name='confirmation_create'),
    path('confirmation/<int:pk>/edit/', views.confirmation_edit, name='confirmation_edit'),
    path('confirmation/<int:pk>/print/', views.confirmation_print, name='confirmation_print'),

    # First Holy Communion
    path('members/<int:member_pk>/communion/add/', views.communion_create, name='communion_create'),
    path('communion/<int:pk>/edit/', views.communion_edit, name='communion_edit'),
    path('communion/<int:pk>/print/', views.communion_print, name='communion_print'),

    # Marriage
    path('members/<int:member_pk>/marriage/add/', views.marriage_create, name='marriage_create'),
    path('marriage/<int:pk>/edit/', views.marriage_edit, name='marriage_edit'),
    path('marriage/<int:pk>/print/', views.marriage_print, name='marriage_print'),

    # Last Rites
    path('members/<int:member_pk>/last-rites/add/', views.last_rites_create, name='last_rites_create'),
    path('last-rites/<int:pk>/edit/', views.last_rites_edit, name='last_rites_edit'),
    path('last-rites/<int:pk>/print/', views.last_rites_print, name='last_rites_print'),

    # Pledges
    path('pledges/', views.pledge_list, name='pledge_list'),
    path('pledges/new/', views.pledge_create, name='pledge_create'),
    path('pledges/<int:pk>/', views.pledge_detail, name='pledge_detail'),
    path('pledges/<int:pk>/edit/', views.pledge_edit, name='pledge_edit'),
    path('pledges/<int:pk>/delete/', views.pledge_delete, name='pledge_delete'),
    path('pledges/<int:pledge_pk>/payment/add/', views.payment_add, name='payment_add'),
    path('payment/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # Print
    path('members/<int:pk>/print/', views.member_print, name='member_print'),
    path('members/print/all/', views.member_list_print, name='member_list_print'),
    path('pledges/<int:pk>/print/', views.pledge_print, name='pledge_print'),
    path('pledges/print/all/', views.pledge_list_print, name='pledge_list_print'),
]
