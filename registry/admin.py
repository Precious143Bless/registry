from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.html import format_html
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment, ParishPriest, ParishOfficer


class CustomUserAdmin(DefaultUserAdmin):
    """Custom User Admin to manage and enforce user roles"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_role_badge', 'is_active')
    list_filter = ('is_active', 'is_superuser', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('User Role & Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'Role Assignment: Admin (superuser), Staff (priests), Member (regular users)'
        }),
        ('Profile Link', {'fields': ('profile_link',), 'classes': ('collapse',)}),
        ('Permissions', {'fields': ('groups', 'user_permissions'), 'classes': ('collapse',)}),
        ('Important Dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('profile_link', 'last_login', 'date_joined')
    
    def user_role_badge(self, obj):
        """Display user role with color-coded badge"""
        if obj.is_superuser:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">Admin</span>'
            )
        elif obj.is_staff:
            if hasattr(obj, 'priest_profile') and obj.priest_profile:
                return format_html(
                    '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">Staff (Priest)</span>'
                )
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">Staff</span>'
            )
        elif hasattr(obj, 'member_profile') and obj.member_profile:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">Member</span>'
            )
        return format_html(
            '<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">No Role</span>'
        )
    user_role_badge.short_description = 'User Role'
    
    def profile_link(self, obj):
        """Show which profile the user is linked to"""
        profiles = []
        if obj.is_superuser:
            profiles.append('✓ Admin (Superuser)')
        if hasattr(obj, 'priest_profile') and obj.priest_profile:
            profiles.append(f'✓ Priest Profile: {obj.priest_profile}')
        if hasattr(obj, 'member_profile') and obj.member_profile:
            profiles.append(f'✓ Member Profile: {obj.member_profile}')
        
        if not profiles:
            return 'No profile linked to this user'
        return '\n'.join(profiles)
    profile_link.short_description = 'Linked Profiles'
    
    def save_model(self, request, obj, form, change):
        """Enforce role system when saving user"""
        # Validate role consistency
        is_priest = hasattr(obj, 'priest_profile') and obj.priest_profile
        is_member = hasattr(obj, 'member_profile') and obj.member_profile
        
        # Priests must be staff
        if is_priest and not obj.is_staff and not obj.is_superuser:
            obj.is_staff = True
        
        # Members must NOT be staff (unless admin)
        if is_member and obj.is_staff and not obj.is_superuser:
            obj.is_staff = False
        
        # Can't be both priest and member
        if is_priest and is_member:
            raise ValueError("User cannot be both a priest and a member.")
        
        super().save_model(request, obj, form, change)


# Replace default User admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ─── Member Admin ────────────────────────────────────────────────────────────

class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'linked_user', 'is_active', 'church_parish_display', 'date_registered')
    list_filter = ('is_active', 'date_registered', 'church', 'parish')
    search_fields = ('first_name', 'last_name', 'email', 'contact_number', 'user__username')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'birthday', 'gender', 'civil_status')
        }),
        ('Contact Information', {
            'fields': ('email', 'contact_number', 'address')
        }),
        ('Assignment', {
            'fields': ('church', 'parish')
        }),
        ('User Account', {
            'fields': ('user', 'user_status'),
            'description': 'Link to Django User account. If linked, user must NOT have is_staff=True'
        }),
        ('Status', {
            'fields': ('is_active', 'date_registered'),
        }),
    )
    readonly_fields = ('date_registered', 'user_status')
    
    def linked_user(self, obj):
        """Show if member has a linked user account"""
        if obj.user:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>',
                obj.user.username
            )
        return format_html('<span style="color: red;">✗ Not linked</span>')
    linked_user.short_description = 'Linked User'
    
    def user_status(self, obj):
        """Display user status information"""
        if not obj.user:
            return 'No user account linked'
        status = 'Active' if obj.user.is_active else 'Inactive'
        role = 'Admin' if obj.user.is_superuser else ('Staff' if obj.user.is_staff else 'Member')
        return f'Username: {obj.user.username} | Status: {status} | Role: {role}'
    user_status.short_description = 'User Status'
    
    def save_model(self, request, obj, form, change):
        """Ensure member's user account is not staff"""
        if obj.user and obj.user.is_staff and not obj.user.is_superuser:
            obj.user.is_staff = False
            obj.user.save()
        super().save_model(request, obj, form, change)


# ─── Priest Admin ────────────────────────────────────────────────────────────

class ParishPriestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'linked_user', 'status', 'church', 'parish', 'date_added')
    list_filter = ('status', 'date_added', 'church', 'parish')
    search_fields = ('first_name', 'last_name', 'email', 'contact_number', 'user__username')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'contact_number', 'email', 'image')
        }),
        ('Priest Details', {
            'fields': ('ordination_date', 'priest_since', 'biography')
        }),
        ('Assignment', {
            'fields': ('church', 'parish', 'date_assigned', 'date_departed')
        }),
        ('User Account', {
            'fields': ('user', 'user_status'),
            'description': 'Link to Django User account. If linked, user MUST have is_staff=True'
        }),
        ('Status & Remarks', {
            'fields': ('status', 'remarks'),
        }),
        ('Metadata', {
            'fields': ('date_added', 'date_updated'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('date_added', 'date_updated', 'user_status')
    
    def linked_user(self, obj):
        """Show if priest has a linked user account"""
        if obj.user:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>',
                obj.user.username
            )
        return format_html('<span style="color: red;">✗ Not linked</span>')
    linked_user.short_description = 'Linked User'
    
    def user_status(self, obj):
        """Display user status information"""
        if not obj.user:
            return 'No user account linked'
        status = 'Active' if obj.user.is_active else 'Inactive'
        is_staff = 'Yes' if obj.user.is_staff else 'NO (ERROR - Should be staff!)'
        return f'Username: {obj.user.username} | Status: {status} | Staff: {is_staff}'
    user_status.short_description = 'User Status'
    
    def save_model(self, request, obj, form, change):
        """Ensure priest's user account is staff"""
        if obj.user and not obj.user.is_staff and not obj.user.is_superuser:
            obj.user.is_staff = True
            obj.user.save()
        super().save_model(request, obj, form, change)


# ─── Other Models ────────────────────────────────────────────────────────────

class BaptismAdmin(admin.ModelAdmin):
    list_display = ('member', 'date_baptized', 'priest')
    search_fields = ('member__first_name', 'member__last_name', 'priest')
    list_filter = ('date_baptized',)


class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ('member', 'date_confirmed', 'bishop', 'confirmation_name')
    search_fields = ('member__first_name', 'member__last_name', 'bishop')
    list_filter = ('date_confirmed',)


class FirstHolyCommunionAdmin(admin.ModelAdmin):
    list_display = ('member', 'date_received', 'priest')
    search_fields = ('member__first_name', 'member__last_name', 'priest')
    list_filter = ('date_received',)


class MarriageAdmin(admin.ModelAdmin):
    list_display = ('member', 'spouse_name', 'date_married', 'priest')
    search_fields = ('member__first_name', 'member__last_name', 'spouse_name', 'priest')
    list_filter = ('date_married',)


class LastRitesAdmin(admin.ModelAdmin):
    list_display = ('member', 'date_administered', 'priest')
    search_fields = ('member__first_name', 'member__last_name', 'priest')
    list_filter = ('date_administered',)


class PledgeAdmin(admin.ModelAdmin):
    list_display = ('member', 'description', 'amount_pledged', 'status', 'due_date')
    search_fields = ('member__first_name', 'member__last_name', 'description')
    list_filter = ('status', 'due_date')
    readonly_fields = ('total_paid', 'balance')


class PledgePaymentAdmin(admin.ModelAdmin):
    list_display = ('pledge', 'amount', 'date_paid')
    search_fields = ('pledge__member__first_name', 'pledge__member__last_name')
    list_filter = ('date_paid',)


class ParishOfficerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'status', 'date_assigned', 'date_added')
    search_fields = ('first_name', 'last_name', 'email', 'position')
    list_filter = ('position', 'status', 'date_assigned')


# ─── Register Models ─────────────────────────────────────────────────────────

admin.site.register(Member, MemberAdmin)
admin.site.register(Baptism, BaptismAdmin)
admin.site.register(Confirmation, ConfirmationAdmin)
admin.site.register(FirstHolyCommunion, FirstHolyCommunionAdmin)
admin.site.register(Marriage, MarriageAdmin)
admin.site.register(LastRites, LastRitesAdmin)
admin.site.register(Pledge, PledgeAdmin)
admin.site.register(PledgePayment, PledgePaymentAdmin)
admin.site.register(ParishPriest, ParishPriestAdmin)
admin.site.register(ParishOfficer, ParishOfficerAdmin)
