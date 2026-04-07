from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Landing
    path('landing/', views.landing_view, name='landing'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Notifications
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Members
    path('members/', views.member_list, name='member_list'),
    path('members/new/', views.member_create, name='member_create'),
    path('members/print/all/', views.member_list_print, name='member_list_print'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/deactivate/', views.member_deactivate, name='member_deactivate'),
    path('members/<int:pk>/reactivate/', views.member_reactivate, name='member_reactivate'),
    path('members/archive/', views.member_archive, name='member_archive'),
    path('members/<int:pk>/print/', views.member_print, name='member_print'),

    # Sacraments
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
    path('members/<int:member_pk>/pledge/add/', views.member_pledge_create, name='member_pledge_create'),
    path('pledges/print/all/', views.pledge_list_print, name='pledge_list_print'),
    path('pledges/<int:pk>/', views.pledge_detail, name='pledge_detail'),
    path('pledges/<int:pk>/edit/', views.pledge_edit, name='pledge_edit'),
    path('pledges/<int:pk>/delete/', views.pledge_delete, name='pledge_delete'),
    path('pledges/<int:pk>/print/', views.pledge_print, name='pledge_print'),
    path('pledges/<int:pledge_pk>/payment/add/', views.payment_add, name='payment_add'),
    path('payment/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('payment/<int:pk>/edit/', views.payment_edit, name='payment_edit'),

    # Donations
    path('donations/new/', views.donation_create, name='donation_create'),
    path('donations/<int:pk>/', views.donation_detail, name='donation_detail'),
    path('donations/<int:pk>/edit/', views.donation_edit, name='donation_edit'),
    path('donations/<int:pk>/delete/', views.donation_delete, name='donation_delete'),
    path('donations/<int:pk>/print/', views.donation_print, name='donation_print'),
    path('donations/print/all/', views.donation_list_print, name='donation_list_print'),

    # Offerings
    path('offerings/new/', views.offering_create, name='offering_create'),
    path('offerings/<int:pk>/', views.offering_detail, name='offering_detail'),
    path('offerings/<int:pk>/edit/', views.offering_edit, name='offering_edit'),
    path('offerings/<int:pk>/delete/', views.offering_delete, name='offering_delete'),
    path('offerings/<int:pk>/print/', views.offering_print, name='offering_print'),
    path('offerings/print/all/', views.offering_list_print, name='offering_list_print'),

    # Accounting combined print
    path('accounting/print/all/', views.accounting_all_print, name='accounting_all_print'),

    # Database Management
    path('database/backup/', views.backup_database, name='database_backup'),
    path('database/restore/', views.restore_database, name='database_restore'),

    # Parish Info
    path('parish-info/', views.parish_info, name='parish_info'),

    # Parish Priests
    path('priests/', views.priests_list, name='priests_list'),
    path('priests/new/', views.priest_create, name='priest_create'),
    path('priests/archive/', views.priest_archive, name='priest_archive'),
    path('priests/print/all/', views.priests_list_print, name='priests_list_print'),
    path('priests/<int:pk>/', views.priest_detail, name='priest_detail'),
    path('priests/<int:pk>/edit/', views.priest_edit, name='priest_edit'),
    path('priests/<int:pk>/deactivate/', views.priest_deactivate, name='priest_deactivate'),
    path('api/parishes/by-church/<int:church_id>/', views.get_parishes_by_church, name='get_parishes_by_church'),
    path('api/parishes/all/', views.get_all_parishes, name='get_all_parishes'),

    # Parish Officers
    path('officers/', views.officers_list, name='officers_list'),
    path('officers/new/', views.officer_create, name='officer_create'),
    path('officers/archive/', views.officer_archive, name='officer_archive'),
    path('officers/print/all/', views.officers_list_print, name='officers_list_print'),
    path('officers/<int:pk>/', views.officer_detail, name='officer_detail'),
    path('officers/<int:pk>/edit/', views.officer_edit, name='officer_edit'),
    path('officers/<int:pk>/deactivate/', views.officer_deactivate, name='officer_deactivate'),
    path('officers/chart/', views.officers_chart, name='officers_chart'),

    # Organizations
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/new/', views.organization_create, name='organization_create'),
    path('organizations/<int:pk>/', views.organization_detail, name='organization_detail'),
    path('organizations/<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('organizations/<int:pk>/delete/', views.organization_delete, name='organization_delete'),

    # Organization Memberships
    path('organizations/<int:org_pk>/add-member/', views.organization_add_member, name='organization_add_member'),
    path('memberships/<int:pk>/edit/', views.membership_edit, name='membership_edit'),
    path('memberships/<int:pk>/delete/', views.membership_delete, name='membership_delete'),

    # Churches
    path('churches/', views.church_list, name='church_list'),
    path('churches/new/', views.church_create, name='church_create'),
    path('churches/<int:pk>/', views.church_detail, name='church_detail'),
    path('churches/<int:pk>/edit/', views.church_edit, name='church_edit'),
    path('churches/<int:pk>/delete/', views.church_delete, name='church_delete'),

    # Parishes
    path('parishes/', views.parish_list, name='parish_list'),
    path('parishes/new/', views.parish_create, name='parish_create'),
    path('parishes/<int:pk>/', views.parish_detail, name='parish_detail'),
    path('parishes/<int:pk>/edit/', views.parish_edit, name='parish_edit'),
    path('parishes/<int:pk>/delete/', views.parish_delete, name='parish_delete'),
    path('parishes/<int:pk>/members/', views.parish_member, name='parish_member'),
    path('parishes/<int:pk>/officer-chart/', views.parish_officer_chart, name='parish_officer_chart'),
    path('parishes/<int:parish_pk>/priests/', views.parish_priest_list, name='parish_priest_list'),
    path('priests/<int:pk>/remove-from-parish/', views.priest_remove_from_parish, name='priest_remove_from_parish'),

    # Parish Officers
    path('parishes/<int:parish_pk>/officer/add/', views.parish_officer_add, name='parish_officer_add'),
    path('parish-officers/<int:pk>/edit/', views.parish_officer_edit, name='parish_officer_edit'),
    path('parish-officers/<int:pk>/delete/', views.parish_officer_delete, name='parish_officer_delete'),

    # Parish Officer Chart and member
    path('parishes/<int:pk>/officer-chart/', views.parish_officer_chart, name='parish_officer_chart'),
    path('parishes/<int:pk>/members/', views.parish_member, name='parish_member'),

    # User Management (Admin only)
    path('users/', views.user_list, name='user_list'),
    path('users/archive/', views.user_archive, name='user_archive'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Cathedrals
    path('cathedrals/', views.cathedral_list, name='cathedral_list'),
    path('cathedrals/new/', views.cathedral_create, name='cathedral_create'),
    path('cathedrals/<int:pk>/', views.cathedral_detail, name='cathedral_detail'),
    path('cathedrals/<int:pk>/edit/', views.cathedral_edit, name='cathedral_edit'),
    path('cathedrals/<int:pk>/delete/', views.cathedral_delete, name='cathedral_delete'),
    
    # Member Portal
    path('member/dashboard/', views.member_dashboard, name='member_dashboard'),
    path('member/profile/', views.member_profile, name='member_profile'),
    path('member/change-password/', views.member_change_password, name='member_change_password'),
    path('member/pledges/', views.member_pledges, name='member_pledges'),
    path('member/pledges/<int:pk>/', views.member_pledge_detail, name='member_pledge_detail'),
    path('member/sacraments/', views.member_sacraments, name='member_sacraments'),
    path('member/organizations/', views.member_organizations, name='member_organizations'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
