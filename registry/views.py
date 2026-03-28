from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User  
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import random
import string
import os
from django.http import JsonResponse
import subprocess
from django.core.paginator import Paginator
from datetime import datetime
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment, ParishInfo, ParishPriest, ParishOfficer, Notification, Organization, OrganizationMembership, Church, Parish, ParishOfficerEP, Cathedral
from .forms import (MemberForm, BaptismForm, ConfirmationForm, CommunionForm,
                    MarriageForm, LastRitesForm, PledgeForm, PledgePaymentForm, ParishInfoForm,ParishPriestForm, ParishOfficerForm, OrganizationForm,OrganizationMembershipForm, ParishOfficerRegistrationForm, ChurchForm, ParishForm, ParishOfficerEPForm, CathedralForm)
from .decorators import admin_required, officer_required  


# ─── AUTH ────────────────────────────────────────────────────────────────────

def landing_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    parish = ParishInfo.objects.first()
    return render(request, 'registry/landing.html', {'parish': parish})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Try to find user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = None
        
        # Authenticate with username
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            
            # Check if user is superuser
            if user.is_superuser:
                messages.success(request, f'Welcome back, Administrator!')
                return redirect('dashboard')
            
            # Check if this user has a parish officer record
            try:
                officer = ParishOfficer.objects.filter(email=user.email).first()
                
                if officer and officer.status == 'active':
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account is not authorized or not active.')
                    logout(request)
                    return render(request, 'registry/login.html')
            except Exception as e:
                print(f"Login error: {e}")
                messages.error(request, 'Your account is not authorized for this system.')
                logout(request)
                return render(request, 'registry/login.html')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'registry/login.html')

def register_view(request):
    """Registration view for parish officers"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ParishOfficerRegistrationForm(request.POST)
        if form.is_valid():
            # Get the officer data
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password']
            
            # Check if this email is registered in ParishOfficer table
            try:
                officer = ParishOfficer.objects.get(email=email)
                
                # Also verify name matches
                if officer.first_name.lower() != first_name.lower() or officer.last_name.lower() != last_name.lower():
                    messages.error(request, 'The name you entered does not match our records for this email.')
                    return render(request, 'registry/register.html', {'form': form})
                
                # Check if officer is active
                if officer.status != 'active':
                    messages.error(request, 'Your account is not active. Please contact the administrator.')
                    return render(request, 'registry/register.html', {'form': form})
                
                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'An account with this email already exists. Please login instead.')
                    return redirect('login')
                
                # Create username from email (without @ symbol)
                username = email.split('@')[0]
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create the user account
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )
                user.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, f'Welcome {first_name}! Your account has been created successfully.')
                return redirect('dashboard')
                
            except ParishOfficer.DoesNotExist:
                messages.error(request, 'You are not authorized to register. Only parish officers can create accounts.')
                return render(request, 'registry/register.html', {'form': form})
            except Exception as e:
                messages.error(request, f'Registration error: {str(e)}')
                return render(request, 'registry/register.html', {'form': form})
    else:
        form = ParishOfficerRegistrationForm()
    
    return render(request, 'registry/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# ─── PASSWORD RESET WITH OTP ─────────────────────────────────────────────────

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def forgot_password(request):
    """Forgot password - request OTP"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            # Check if user exists
            user = User.objects.get(email=email)
            
            # Check if user is a parish officer or admin
            is_authorized = False
            if user.is_superuser:
                is_authorized = True
            else:
                officer = ParishOfficer.objects.filter(email=email).first()
                if officer and officer.status == 'active':
                    is_authorized = True
            
            if is_authorized:
                # Generate OTP
                otp = generate_otp()
                
                # Store OTP in session (expires after 10 minutes)
                request.session['reset_otp'] = otp
                request.session['reset_email'] = email
                request.session['reset_otp_time'] = datetime.now().timestamp()
                
                # Send OTP via email
                subject = 'Password Reset OTP - Parish Registry System'
                message = f"""
                Dear {user.first_name or user.username},

                You have requested to reset your password for the Parish Registry System.

                Your OTP (One-Time Password) is: {otp}

                This OTP is valid for 10 minutes.

                If you did not request this, please ignore this email.

                Thank you,
                Parish Registry System
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL or 'noreply@parish.com',
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, f'An OTP has been sent to {email}. Please check your inbox.')
                    return redirect('verify_otp')
                except Exception as e:
                    messages.error(request, f'Failed to send email. Please try again later. Error: {str(e)}')
            else:
                messages.error(request, 'This email is not authorized to reset password.')
                
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'registry/forgot_password/forgot_password.html')

def verify_otp(request):
    """Verify OTP sent to email"""
    if 'reset_otp' not in request.session:
        messages.error(request, 'Please request a password reset first.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('reset_otp')
        otp_time = request.session.get('reset_otp_time')
        
        # Check if OTP is expired (10 minutes)
        if otp_time and (datetime.now().timestamp() - float(otp_time)) > 600:
            del request.session['reset_otp']
            del request.session['reset_email']
            del request.session['reset_otp_time']
            messages.error(request, 'OTP has expired. Please request a new one.')
            return redirect('forgot_password')
        
        if entered_otp == stored_otp:
            # OTP verified, proceed to reset password
            messages.success(request, 'OTP verified. You can now reset your password.')
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'registry/forgot_password/verify_otp.html')

def reset_password(request):
    """Reset password after OTP verification"""
    if 'reset_email' not in request.session:
        messages.error(request, 'Please request a password reset first.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registry/forgot_password/reset_password.html')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'registry/forgot_password/reset_password.html')
        
        try:
            email = request.session['reset_email']
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Clear session data
            del request.session['reset_otp']
            del request.session['reset_email']
            del request.session['reset_otp_time']
            
            messages.success(request, 'Password reset successfully. Please login with your new password.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')
    
    return render(request, 'registry/forgot_password/reset_password.html')

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    context = {
        'total_members':       Member.objects.filter(is_active=True).count(),
        'total_baptisms':      Baptism.objects.count(),
        'total_confirmations': Confirmation.objects.count(),
        'total_communions':    FirstHolyCommunion.objects.count(),
        'total_marriages':     Marriage.objects.count(),
        'total_last_rites':    LastRites.objects.count(),
        'total_pledges':       Pledge.objects.count(),
        'outstanding_pledges': Pledge.objects.filter(status__in=['unpaid', 'partial']).count(),
        'recent_members':      Member.objects.filter(is_active=True).order_by('-date_registered')[:5],
    }
    return render(request, 'registry/dashboard.html', context)


# ─── NOTIFICATIONS ───────────────────────────────────────────────────────────

@login_required
@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@csrf_exempt
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# ─── MEMBERS ─────────────────────────────────────────────────────────────────

@login_required
def member_list(request):
    from django.core.paginator import Paginator
    
    q = request.GET.get('q', '')
    church_filter = request.GET.get('church_filter', '')
    parish_filter = request.GET.get('parish_filter', '')
    
    members = Member.objects.filter(is_active=True)
    
    # Search by name or contact
    if q:
        members = members.filter(
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) | 
            Q(contact_number__icontains=q)
        )
    
    # Filter by church
    if church_filter:
        members = members.filter(church_id=church_filter)
    
    # Filter by parish
    if parish_filter:
        members = members.filter(parish_id=parish_filter)
    
    # Get all churches for filter dropdown
    churches = Church.objects.filter(is_active=True).order_by('name')
    
    # Get all parishes for filter dropdown
    parishes = Parish.objects.filter(is_active=True).order_by('name')
    
    # Pagination
    paginator = Paginator(members, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Get filter names for display
    church_filter_name = None
    parish_filter_name = None
    if church_filter:
        try:
            church_filter_name = Church.objects.get(id=church_filter).name
        except Church.DoesNotExist:
            pass
    if parish_filter:
        try:
            parish_filter_name = Parish.objects.get(id=parish_filter).name
        except Parish.DoesNotExist:
            pass
    
    return render(request, 'registry/members/list.html', {
        'members': page_obj,
        'page_obj': page_obj,
        'q': q,
        'church_filter': church_filter,
        'parish_filter': parish_filter,
        'church_filter_name': church_filter_name,
        'parish_filter_name': parish_filter_name,
        'churches': churches,
        'parishes': parishes,
    })


@login_required
def member_create(request):
    form = MemberForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Member registered successfully.')
        return redirect('member_list')
    return render(request, 'registry/members/form.html', {'form': form, 'title': 'Register New Member'})


@login_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'registry/members/detail.html', {'member': member})


@login_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    form = MemberForm(request.POST or None, instance=member)
    if form.is_valid():
        form.save()
        messages.success(request, 'Member updated successfully.')
        return redirect('member_detail', pk=pk)
    return render(request, 'registry/members/form.html', {'form': form, 'title': 'Edit Member', 'member': member})


@login_required
def member_deactivate(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.is_active = False
        member.save()
        messages.success(request, f'{member.full_name} has been deactivated.')
        return redirect('member_list')
    return render(request, 'registry/confirm_delete.html', {'object': member, 'type': 'Member'})


@login_required
def member_archive(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    members = Member.objects.filter(is_active=False)
    if q:
        members = members.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) | Q(contact_number__icontains=q)
        )
    paginator = Paginator(members, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'registry/members/archive.html', {'members': page_obj, 'page_obj': page_obj, 'q': q})


@login_required
def member_reactivate(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.is_active = True
        member.save()
        messages.success(request, f'{member.full_name} has been reactivated.')
        return redirect('member_archive')
    return redirect('member_archive')


# ─── SACRAMENTS ──────────────────────────────────────────────────────────────

def _parish_ctx():
    """Helper to inject ParishInfo into print views."""
    return ParishInfo.objects.first()


@login_required
def sacrament_list(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    baptisms      = Baptism.objects.select_related('member')
    confirmations = Confirmation.objects.select_related('member')
    communions    = FirstHolyCommunion.objects.select_related('member')
    marriages     = Marriage.objects.select_related('member')
    last_rites    = LastRites.objects.select_related('member')
    if q:
        f = Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q)
        baptisms      = baptisms.filter(f)
        confirmations = confirmations.filter(f)
        communions    = communions.filter(f)
        marriages     = marriages.filter(f | Q(spouse_name__icontains=q))
        last_rites    = last_rites.filter(f)

    def paginate(qs, param):
        return Paginator(qs, 15).get_page(request.GET.get(param))

    context = {
        'baptisms':      paginate(baptisms,      'page_b'),
        'confirmations': paginate(confirmations, 'page_c'),
        'communions':    paginate(communions,    'page_co'),
        'marriages':     paginate(marriages,     'page_m'),
        'last_rites':    paginate(last_rites,    'page_lr'),
        'q': q,
        'all_members': Member.objects.filter(is_active=True).order_by('last_name', 'first_name'),
    }
    return render(request, 'registry/sacraments/list.html', context)


@login_required
def baptism_create(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    if hasattr(member, 'baptism'):
        messages.warning(request, 'This member already has a baptism record.')
        return redirect('member_detail', pk=member_pk)
    form = BaptismForm(request.POST or None)
    if form.is_valid():
        b = form.save(commit=False)
        b.member = member
        b.save()
        messages.success(request, 'Baptism record saved.')
        return redirect('member_detail', pk=member_pk)
    return render(request, 'registry/sacraments/form_baptism.html', {'form': form, 'member': member, 'title': 'Add Baptism Record'})


@login_required
def baptism_edit(request, pk):
    baptism = get_object_or_404(Baptism, pk=pk)
    form = BaptismForm(request.POST or None, instance=baptism)
    if form.is_valid():
        form.save()
        messages.success(request, 'Baptism record updated.')
        return redirect('member_detail', pk=baptism.member.pk)
    return render(request, 'registry/sacraments/form_baptism.html', {'form': form, 'member': baptism.member, 'title': 'Edit Baptism Record'})


@login_required
def baptism_print(request, pk):
    return render(request, 'registry/sacraments/print_baptism.html', {
        'baptism': get_object_or_404(Baptism, pk=pk),
        'parish': _parish_ctx(),
    })


@login_required
def confirmation_create(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    if hasattr(member, 'confirmation'):
        messages.warning(request, 'This member already has a confirmation record.')
        return redirect('member_detail', pk=member_pk)
    form = ConfirmationForm(request.POST or None)
    if form.is_valid():
        c = form.save(commit=False)
        c.member = member
        c.save()
        messages.success(request, 'Confirmation record saved.')
        return redirect('member_detail', pk=member_pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': member, 'title': 'Add Confirmation Record'})


@login_required
def confirmation_edit(request, pk):
    conf = get_object_or_404(Confirmation, pk=pk)
    form = ConfirmationForm(request.POST or None, instance=conf)
    if form.is_valid():
        form.save()
        messages.success(request, 'Confirmation record updated.')
        return redirect('member_detail', pk=conf.member.pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': conf.member, 'title': 'Edit Confirmation Record'})


@login_required
def confirmation_print(request, pk):
    conf = get_object_or_404(Confirmation, pk=pk)
    return render(request, 'registry/sacraments/print_confirmation.html', {
        'conf': conf,
        'parish': _parish_ctx(),
    })


@login_required
def communion_create(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    if hasattr(member, 'communion'):
        messages.warning(request, 'This member already has a communion record.')
        return redirect('member_detail', pk=member_pk)
    form = CommunionForm(request.POST or None)
    if form.is_valid():
        c = form.save(commit=False)
        c.member = member
        c.save()
        messages.success(request, 'First Holy Communion record saved.')
        return redirect('member_detail', pk=member_pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': member, 'title': 'Add First Holy Communion Record'})


@login_required
def communion_edit(request, pk):
    communion = get_object_or_404(FirstHolyCommunion, pk=pk)
    form = CommunionForm(request.POST or None, instance=communion)
    if form.is_valid():
        form.save()
        messages.success(request, 'Communion record updated.')
        return redirect('member_detail', pk=communion.member.pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': communion.member, 'title': 'Edit Communion Record'})


@login_required
def communion_print(request, pk):
    communion = get_object_or_404(FirstHolyCommunion, pk=pk)
    return render(request, 'registry/sacraments/print_communion.html', {
        'communion': communion,
        'parish': _parish_ctx(),
    })


@login_required
def marriage_create(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    form = MarriageForm(request.POST or None)
    if form.is_valid():
        m = form.save(commit=False)
        m.member = member
        m.save()
        messages.success(request, 'Marriage record saved.')
        return redirect('member_detail', pk=member_pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': member, 'title': 'Add Marriage Record'})


@login_required
def marriage_edit(request, pk):
    marriage = get_object_or_404(Marriage, pk=pk)
    form = MarriageForm(request.POST or None, instance=marriage)
    if form.is_valid():
        form.save()
        messages.success(request, 'Marriage record updated.')
        return redirect('member_detail', pk=marriage.member.pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': marriage.member, 'title': 'Edit Marriage Record'})


@login_required
def marriage_print(request, pk):
    marriage = get_object_or_404(Marriage, pk=pk)
    return render(request, 'registry/sacraments/print_marriage.html', {
        'marriage': marriage,
        'parish': _parish_ctx(),
    })


@login_required
def last_rites_create(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    if hasattr(member, 'last_rites'):
        messages.warning(request, 'This member already has a last rites record.')
        return redirect('member_detail', pk=member_pk)
    form = LastRitesForm(request.POST or None)
    if form.is_valid():
        lr = form.save(commit=False)
        lr.member = member
        lr.save()
        messages.success(request, 'Last Rites record saved.')
        return redirect('member_detail', pk=member_pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': member, 'title': 'Add Last Rites Record'})


@login_required
def last_rites_edit(request, pk):
    lr = get_object_or_404(LastRites, pk=pk)
    form = LastRitesForm(request.POST or None, instance=lr)
    if form.is_valid():
        form.save()
        messages.success(request, 'Last Rites record updated.')
        return redirect('member_detail', pk=lr.member.pk)
    return render(request, 'registry/sacraments/form.html', {'form': form, 'member': lr.member, 'title': 'Edit Last Rites Record'})


@login_required
def last_rites_print(request, pk):
    lr = get_object_or_404(LastRites, pk=pk)
    return render(request, 'registry/sacraments/print_last_rites.html', {
        'lr': lr,
        'parish': _parish_ctx(),
    })


# ─── PLEDGES ─────────────────────────────────────────────────────────────────

@login_required
def pledge_list(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    pledges = Pledge.objects.select_related('member')
    if q:
        pledges = pledges.filter(
            Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) |
            Q(description__icontains=q)
        )
    paginator = Paginator(pledges, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'registry/pledges/list.html', {
        'pledges': page_obj,
        'page_obj': page_obj,
        'q': q,
        'all_members': Member.objects.filter(is_active=True).order_by('last_name', 'first_name'),
    })


@login_required
def pledge_create(request):
    form = PledgeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pledge recorded successfully.')
        return redirect('pledge_list')
    if request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field.replace("_", " ").title()}: {error}')
        return redirect('pledge_list')
    return render(request, 'registry/pledges/form.html', {'form': form, 'title': 'Add Pledge'})


@login_required
def member_pledge_create(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    if request.method == 'POST':
        from datetime import date as _date
        description = request.POST.get('description', '').strip()
        amount = request.POST.get('amount_pledged', '')
        due_date = request.POST.get('due_date', '')
        errors = []
        if not description or len(description) < 3:
            errors.append('Description must be at least 3 characters.')
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                errors.append('Amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Enter a valid amount.')
        try:
            due_date_val = _date.fromisoformat(due_date)
            if due_date_val < _date.today():
                errors.append('Due date cannot be in the past.')
        except (ValueError, TypeError):
            errors.append('Enter a valid due date.')
        if not errors:
            Pledge.objects.create(
                member=member,
                description=description,
                amount_pledged=amount_val,
                due_date=due_date_val,
            )
            messages.success(request, 'Pledge recorded successfully.')
        else:
            for e in errors:
                messages.error(request, e)
    return redirect('member_detail', pk=member_pk)


@login_required
def pledge_detail(request, pk):
    from django.core.paginator import Paginator
    pledge = get_object_or_404(Pledge, pk=pk)
    payments = pledge.payments.all()

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    amount_min = request.GET.get('amount_min', '')
    amount_max = request.GET.get('amount_max', '')

    if date_from:
        payments = payments.filter(date_paid__gte=date_from)
    if date_to:
        payments = payments.filter(date_paid__lte=date_to)
    if amount_min:
        payments = payments.filter(amount__gte=amount_min)
    if amount_max:
        payments = payments.filter(amount__lte=amount_max)

    paginator = Paginator(payments, 7)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'registry/pledges/detail.html', {
        'pledge': pledge,
        'page_obj': page,
        'date_from': date_from,
        'date_to': date_to,
        'amount_min': amount_min,
        'amount_max': amount_max,
    })


@login_required
def pledge_edit(request, pk):
    pledge = get_object_or_404(Pledge, pk=pk)
    form = PledgeForm(request.POST or None, instance=pledge)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pledge updated.')
        return redirect('pledge_list')
    return render(request, 'registry/pledges/form.html', {'form': form, 'title': 'Edit Pledge'})


@login_required
def pledge_delete(request, pk):
    pledge = get_object_or_404(Pledge, pk=pk)
    if request.method == 'POST':
        pledge.delete()
        messages.success(request, 'Pledge deleted.')
        return redirect('pledge_list')
    return render(request, 'registry/confirm_delete.html', {'object': pledge, 'type': 'Pledge'})


@login_required
def payment_add(request, pledge_pk):
    pledge = get_object_or_404(Pledge, pk=pledge_pk)
    if request.method == 'POST':
        form = PledgePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.pledge = pledge
            payment.save()
            messages.success(request, 'Payment recorded.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
        return redirect('pledge_detail', pk=pledge_pk)


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(PledgePayment, pk=pk)
    pledge = payment.pledge
    pledge_pk = pledge.pk
    if request.method == 'POST':
        payment.delete()
        pledge.update_status()
        messages.success(request, 'Payment removed.')
        return redirect('pledge_detail', pk=pledge_pk)
    return render(request, 'registry/confirm_delete.html', {'object': payment, 'type': 'Payment'})


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(PledgePayment, pk=pk)
    form = PledgePaymentForm(request.POST or None, instance=payment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Payment updated.')
        return redirect('pledge_detail', pk=payment.pledge.pk)
    return redirect('pledge_detail', pk=payment.pledge.pk)


# ─── ADMIN-ONLY VIEWS (PARISH PRIESTS) ───────────────────────────────────────

@admin_required
def priests_list(request):
    from django.core.paginator import Paginator
    
    q = request.GET.get('q', '')
    church_filter = request.GET.get('church_filter', '')
    parish_filter = request.GET.get('parish_filter', '')
    
    priests = ParishPriest.objects.all()
    
    # Search by name
    if q:
        priests = priests.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) |
            Q(contact_number__icontains=q) |
            Q(email__icontains=q)
        )
    
    # Filter by church
    if church_filter:
        priests = priests.filter(church_id=church_filter)
    
    # Filter by parish
    if parish_filter:
        priests = priests.filter(parish_id=parish_filter)
    
    # Get all churches for filter dropdown
    churches = Church.objects.filter(is_active=True).order_by('name')
    
    # Get all parishes for filter dropdown
    parishes = Parish.objects.filter(is_active=True).order_by('name')
    
    # Pagination
    paginator = Paginator(priests, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Get filter names for display
    church_filter_name = None
    parish_filter_name = None
    if church_filter:
        try:
            church_filter_name = Church.objects.get(id=church_filter).name
        except Church.DoesNotExist:
            pass
    if parish_filter:
        try:
            parish_filter_name = Parish.objects.get(id=parish_filter).name
        except Parish.DoesNotExist:
            pass
    
    return render(request, 'registry/priests/list.html', {
        'priests': page_obj,
        'page_obj': page_obj,
        'q': q,
        'church_filter': church_filter,
        'parish_filter': parish_filter,
        'church_filter_name': church_filter_name,
        'parish_filter_name': parish_filter_name,
        'churches': churches,
        'parishes': parishes,
    })


@admin_required
def priest_create(request):
    if request.method == 'POST':
        form = ParishPriestForm(request.POST, request.FILES)
        if form.is_valid():
            priest = form.save(commit=False)
            # Handle image clearing if needed
            if request.POST.get('clear_image') == 'on':
                priest.image = None
            priest.save()
            messages.success(request, 'Parish priest added successfully.')
            return redirect('priests_list')
        else:
            # Log form errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
    else:
        form = ParishPriestForm()
    
    return render(request, 'registry/priests/form.html', {
        'form': form,
        'title': 'Add Parish Priest'
    })


@admin_required
def priest_edit(request, pk):
    priest = get_object_or_404(ParishPriest, pk=pk)
    
    if request.method == 'POST':
        form = ParishPriestForm(request.POST, request.FILES, instance=priest)
        if form.is_valid():
            # Handle image clearing
            if request.POST.get('clear_image') == 'on':
                if priest.image:
                    priest.image.delete(save=False)
                form.instance.image = None
            form.save()
            messages.success(request, 'Parish priest updated successfully.')
            return redirect('priest_detail', pk=priest.pk)
        else:
            # Log form errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
    else:
        form = ParishPriestForm(instance=priest)
    
    return render(request, 'registry/priests/form.html', {
        'form': form,
        'title': 'Edit Parish Priest',
        'priest': priest
    })


@admin_required
def priest_detail(request, pk):
    priest = get_object_or_404(ParishPriest, pk=pk)
    return render(request, 'registry/priests/detail.html', {'priest': priest})


@admin_required
def priest_deactivate(request, pk):
    priest = get_object_or_404(ParishPriest, pk=pk)
    if request.method == 'POST':
        if priest.status == 'active':
            priest.status = 'inactive'
            messages.success(request, f'Fr. {priest.last_name} has been deactivated.')
        else:
            priest.status = 'active'
            messages.success(request, f'Fr. {priest.last_name} has been reactivated.')
        priest.save()
        return redirect('priests_list')
    return redirect('priest_detail', pk=pk)


@admin_required
def priests_list_print(request):
    priests = ParishPriest.objects.all().order_by('last_name', 'first_name')
    return render(request, 'registry/priests/print_priest_list.html', {'priests': priests})


@admin_required
def priest_archive(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    priests = ParishPriest.objects.filter(status='inactive')
    if q:
        priests = priests.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(middle_name__icontains=q)
        )
    paginator = Paginator(priests, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'registry/priests/archive.html', {'priests': page_obj, 'page_obj': page_obj, 'q': q})


# ─── ADMIN-ONLY VIEWS (PARISH OFFICERS) ─────────────────────────────────────

@admin_required
def officers_list(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    officers = ParishOfficer.objects.filter(status='active')
    if q:
        officers = officers.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) |
            Q(position__icontains=q) |
            Q(email__icontains=q) |
            Q(contact_number__icontains=q)
        )
    paginator = Paginator(officers, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'registry/officers/list.html', {
        'officers': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


@admin_required
def officer_create(request):
    form = ParishOfficerForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Parish officer added successfully.')
        return redirect('officers_list')
    members = Member.objects.filter(is_active=True).order_by('last_name', 'first_name')
    return render(request, 'registry/officers/form.html', {
        'form': form,
        'title': 'Add Parish Officer',
        'members': members,
    })


@admin_required
def officer_detail(request, pk):
    officer = get_object_or_404(ParishOfficer, pk=pk)
    return render(request, 'registry/officers/detail.html', {'officer': officer})


@admin_required
def officer_edit(request, pk):
    officer = get_object_or_404(ParishOfficer, pk=pk)
    form = ParishOfficerForm(request.POST or None, request.FILES or None, instance=officer)
    if form.is_valid():
        if request.POST.get('clear_image') == 'on':
            if officer.image:
                officer.image.delete(save=False)
            form.instance.image = None
        form.save()
        messages.success(request, 'Parish officer updated successfully.')
        return redirect('officer_detail', pk=officer.pk)
    return render(request, 'registry/officers/form.html', {'form': form, 'title': 'Edit Parish Officer', 'officer': officer})


@admin_required
def officer_deactivate(request, pk):
    officer = get_object_or_404(ParishOfficer, pk=pk)
    if request.method == 'POST':
        if officer.status == 'active':
            officer.status = 'inactive'
            messages.success(request, f'{officer.full_name} has been deactivated.')
        else:
            officer.status = 'active'
            messages.success(request, f'{officer.full_name} has been reactivated.')
        officer.save()
        return redirect('officers_list')
    return render(request, 'registry/officers/confirm_status.html', {'officer': officer})


@admin_required
def officers_list_print(request):
    officers = ParishOfficer.objects.all().order_by('last_name', 'first_name')
    return render(request, 'registry/officers/print_officer_list.html', {'officers': officers})


@admin_required
def officer_archive(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    officers = ParishOfficer.objects.filter(status='inactive')
    if q:
        officers = officers.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) | Q(position__icontains=q)
        )
    paginator = Paginator(officers, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'registry/officers/archive.html', {'officers': page_obj, 'page_obj': page_obj, 'q': q})


@login_required
def officers_chart(request):
    # Define hierarchy levels
    hierarchy = {
        'clergy': {
            'title': 'Clergy',
            'icon': 'bi-church',
            'positions': ['parish_priest', 'parochial_vicar']
        },
        'parish_pastoral_council': {
            'title': 'Parish Pastoral Council',
            'icon': 'bi-building',
            'positions': ['ppc_president', 'ppc_vice_president', 'ppc_secretary', 'ppc_treasurer', 'ppc_auditor']
        },
        'parish_finance_council': {
            'title': 'Parish Finance Council',
            'icon': 'bi-calculator',
            'positions': ['finance_council']
        },
        'administration': {
            'title': 'Administration',
            'icon': 'bi-person-badge',
            'positions': ['parish_secretary', 'parish_administrator', 'social_communications']
        },
        'liturgical_ministries': {
            'title': 'Liturgical Ministries',
            'icon': 'bi-book',
            'positions': ['lector', 'commentator', 'altar_servers', 'choir', 'extraordinary_ministers', 'ushers', 'collectors', 'sacristan', 'church_decorators']
        },
        'faith_formation': {
            'title': 'Faith Formation',
            'icon': 'bi-mortarboard',
            'positions': ['catechists', 'religious_education']
        },
        'pastoral_ministries': {
            'title': 'Pastoral Ministries',
            'icon': 'bi-heart',
            'positions': ['youth_ministry', 'family_ministry', 'womens_ministry', 'mens_ministry']
        },
        'coordinators': {
            'title': 'Coordinators',
            'icon': 'bi-people',
            'positions': ['ministry_coordinators']
        }
    }
    
    # Fetch officers for each category
    chart_data = {}
    for key, category in hierarchy.items():
        officers_in_category = ParishOfficer.objects.filter(
            position__in=category['positions'],
            status='active'
        ).order_by('position')
        
        # Group officers by specific position
        grouped_officers = {}
        for officer in officers_in_category:
            pos_display = officer.get_position_display()
            if pos_display not in grouped_officers:
                grouped_officers[pos_display] = []
            grouped_officers[pos_display].append(officer)
        
        chart_data[key] = {
            'title': category['title'],
            'icon': category['icon'],
            'groups': grouped_officers,
            'count': officers_in_category.count()
        }
    
    # Get parish priest for top-level display
    parish_priest = ParishOfficer.objects.filter(position='parish_priest', status='active').first()
    parochial_vicar = ParishOfficer.objects.filter(position='parochial_vicar', status='active').first()
    
    context = {
        'chart_data': chart_data,
        'parish_priest': parish_priest,
        'parochial_vicar': parochial_vicar,
        'total_officers': ParishOfficer.objects.filter(status='active').count(),
    }
    
    return render(request, 'registry/officers/officers_chart.html', context)


# ─── PRINT VIEWS ─────────────────────────────────────────────────────────────

@login_required
def member_print(request, pk):
    return render(request, 'registry/members/print_member.html', {
        'member': get_object_or_404(Member, pk=pk),
        'parish': _parish_ctx(),
    })


@login_required
def member_list_print(request):
    members = Member.objects.filter(is_active=True).order_by('last_name', 'first_name')
    return render(request, 'registry/members/print_member_list.html', {
        'members': members,
        'parish': _parish_ctx(),
    })


@login_required
def pledge_print(request, pk):
    return render(request, 'registry/pledges/print_pledge.html', {
        'pledge': get_object_or_404(Pledge, pk=pk),
        'parish': _parish_ctx(),
    })


@login_required
def pledge_list_print(request):
    pledges = Pledge.objects.select_related('member').order_by('member__last_name')
    return render(request, 'registry/pledges/print_pledge_list.html', {
        'pledges': pledges,
        'parish': _parish_ctx(),
    })


# ─── ADMIN-ONLY VIEWS (DATABASE MANAGEMENT) ─────────────────────────────────

@admin_required
def backup_database(request):
    if request.method == 'POST':
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'church_registry_backup_{timestamp}.sql'
            backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_filename)
            
            # Ensure backups directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Get database settings from settings.py
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']
            
            # XAMPP MySQL path for Windows
            xampp_mysql_path = r'C:\xampp\mysql\bin'
            mysqldump_cmd = [
                os.path.join(xampp_mysql_path, 'mysqldump.exe'),
                f'--user={db_user}',
                f'--password={db_password}',
                f'--host={db_host}',
                f'--port={db_port}',
                '--single-transaction',
                '--routines',
                '--triggers',
                db_name
            ]
            
            # Execute backup
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                subprocess.run(mysqldump_cmd, stdout=backup_file, check=True, text=True)
            
            messages.success(request, f'Database backup created successfully: {backup_filename}')
            
            # Return the backup file for download
            with open(backup_path, 'rb') as backup_file:
                response = HttpResponse(backup_file.read(), content_type='application/sql')
                response['Content-Disposition'] = f'attachment; filename="{backup_filename}"'
                return response
                
        except Exception as e:
            messages.error(request, f'Backup failed: {str(e)}')
    
    return render(request, 'registry/backup.html')


@admin_required
def restore_database(request):
    if request.method == 'POST':
        try:
            backup_file = request.FILES.get('backup_file')
            if not backup_file:
                messages.error(request, 'Please select a backup file to restore.')
                return render(request, 'registry/restore.html')
            
            # Validate file extension
            if not backup_file.name.endswith('.sql'):
                messages.error(request, 'Please upload a valid SQL backup file.')
                return render(request, 'registry/restore.html')
            
            # Save uploaded file temporarily
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_filename = f'temp_restore_{timestamp}.sql'
            temp_path = os.path.join(settings.BASE_DIR, 'temp', temp_filename)
            
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, 'wb') as temp_file:
                for chunk in backup_file.chunks():
                    temp_file.write(chunk)
            
            # Get database settings
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']
            
            # XAMPP MySQL path for Windows
            xampp_mysql_path = r'C:\xampp\mysql\bin'
            mysql_cmd = [
                os.path.join(xampp_mysql_path, 'mysql.exe'),
                f'--user={db_user}',
                f'--password={db_password}',
                f'--host={db_host}',
                f'--port={db_port}',
                db_name
            ]
            
            # Execute restore
            with open(temp_path, 'r') as restore_file:
                subprocess.run(mysql_cmd, stdin=restore_file, check=True)
            
            # Clean up temp file
            os.remove(temp_path)
            
            messages.success(request, 'Database restored successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Restore failed: {str(e)}')
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
    
    return render(request, 'registry/restore.html')


# ─── ADMIN-ONLY VIEWS (PARISH INFO) ─────────────────────────────────────────

@admin_required
def parish_info(request):
    info = ParishInfo.objects.first()
    churches = Church.objects.all().order_by('name')
    if request.method == 'POST':
        form = ParishInfoForm(request.POST, request.FILES, instance=info)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parish information updated successfully.')
            return redirect('parish_info')
    else:
        form = ParishInfoForm(instance=info)
    return render(request, 'registry/info/detail.html', {
        'info': info,
        'form': form,
        'churches': churches,
    })


# ─── ADMIN-ONLY VIEWS (ORGANIZATIONS) ───────────────────────────────────────

@admin_required
def organization_list(request):
    q = request.GET.get('q', '')
    organizations = Organization.objects.all()
    
    if q:
        organizations = organizations.filter(
            Q(name__icontains=q) | 
            Q(description__icontains=q) |
            Q(contact_person__icontains=q)
        )
    
    return render(request, 'registry/organizations/list.html', {
        'organizations': organizations,
        'q': q,
        'all_members': Member.objects.filter(is_active=True).order_by('last_name', 'first_name'),
    })


@admin_required
def organization_create(request):
    form = OrganizationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Organization created successfully.')
        return redirect('organization_list')
    return render(request, 'registry/organizations/form.html', {
        'form': form,
        'title': 'Add New Organization'
    })


@admin_required
def organization_detail(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    memberships = organization.memberships.select_related('member').all()
    
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    if role_filter:
        memberships = memberships.filter(role=role_filter)
    if status_filter:
        memberships = memberships.filter(is_active=(status_filter == 'active'))
    
    return render(request, 'registry/organizations/detail.html', {
        'organization': organization,
        'memberships': memberships,
        'role_filter': role_filter,
        'status_filter': status_filter,
    })


@admin_required
def organization_edit(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    form = OrganizationForm(request.POST or None, instance=organization)
    if form.is_valid():
        form.save()
        messages.success(request, 'Organization updated successfully.')
        return redirect('organization_detail', pk=organization.pk)
    return render(request, 'registry/organizations/form.html', {
        'form': form,
        'title': 'Edit Organization',
        'organization': organization
    })


@admin_required
def organization_delete(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        organization.delete()
        messages.success(request, f'Organization "{organization.name}" has been deleted.')
        return redirect('organization_list')
    return render(request, 'registry/organizations/confirm_delete.html', {
        'organization': organization
    })


# ─── ADMIN-ONLY VIEWS (ORGANIZATION MEMBERSHIPS) ────────────────────────────

@admin_required
def organization_add_member(request, org_pk):
    organization = get_object_or_404(Organization, pk=org_pk)
    form = OrganizationMembershipForm(request.POST or None)
    
    if form.is_valid():
        membership = form.save(commit=False)
        membership.organization = organization
        
        # Check for duplicate membership
        if OrganizationMembership.objects.filter(
            member=membership.member, 
            organization=organization
        ).exists():
            messages.error(request, f'{membership.member.full_name} is already a member of this organization.')
        else:
            membership.save()
            messages.success(request, f'{membership.member.full_name} has been added to {organization.name}.')
            return redirect('organization_detail', pk=organization.pk)
    
    return render(request, 'registry/organizations/membership_form.html', {
        'form': form,
        'organization': organization,
        'title': f'Add Member to {organization.name}'
    })


@admin_required
def membership_edit(request, pk):
    membership = get_object_or_404(OrganizationMembership, pk=pk)
    form = OrganizationMembershipForm(request.POST or None, instance=membership)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Membership updated successfully.')
        return redirect('organization_detail', pk=membership.organization.pk)
    
    return render(request, 'registry/organizations/membership_form.html', {
        'form': form,
        'organization': membership.organization,
        'membership': membership,
        'title': 'Edit Membership'
    })


@admin_required
def membership_delete(request, pk):
    membership = get_object_or_404(OrganizationMembership, pk=pk)
    organization_pk = membership.organization.pk
    member_name = membership.member.full_name
    org_name = membership.organization.name
    
    if request.method == 'POST':
        membership.delete()
        messages.success(request, f'{member_name} has been removed from {org_name}.')
        return redirect('organization_detail', pk=organization_pk)
    
    return render(request, 'registry/organizations/confirm_membership_delete.html', {
        'membership': membership
    })


@admin_required
def church_list(request):
    q = request.GET.get('q', '')
    churches = Church.objects.all()
    
    if q:
        churches = churches.filter(
            Q(name__icontains=q) |
            Q(location__icontains=q)
        )
    
    paginator = Paginator(churches, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'churches': page_obj,
        'page_obj': page_obj,
        'q': q,
        'total_churches': Church.objects.count(),
        'active_churches': Church.objects.filter(is_active=True).count(),
        'total_parishes': Parish.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'registry/churches/list.html', context)


@admin_required
def church_create(request):
    if request.method == 'POST':
        form = ChurchForm(request.POST, request.FILES)
        if form.is_valid():
            church = form.save()
            messages.success(request, 'Church created successfully.')
            return redirect('church_detail', pk=church.pk)
    else:
        form = ChurchForm()
    
    return render(request, 'registry/churches/form.html', {
        'form': form,
        'title': 'Add New Church'
    })


@admin_required
def church_detail(request, pk):
    church = get_object_or_404(Church, pk=pk)
    parishes = church.parishes.filter(is_active=True).order_by('name')
    cathedral = None
    
    # Check if church has a cathedral
    if hasattr(church, 'cathedral'):
        cathedral = church.cathedral
    
    # Calculate total officers across all parishes
    total_officers = 0
    for parish in parishes:
        total_officers += parish.officer_count
    
    return render(request, 'registry/churches/detail.html', {
        'church': church,
        'parishes': parishes,
        'cathedral': cathedral,
        'total_officers': total_officers,
    })


@admin_required
def church_edit(request, pk):
    church = get_object_or_404(Church, pk=pk)
    
    if request.method == 'POST':
        form = ChurchForm(request.POST, request.FILES, instance=church)
        if form.is_valid():
            # Handle image clearing
            if request.POST.get('clear_image') == 'on':
                if church.image:
                    church.image.delete(save=False)
                form.instance.image = None
            form.save()
            messages.success(request, 'Church updated successfully.')
            return redirect('church_detail', pk=church.pk)
    else:
        form = ChurchForm(instance=church)
    
    return render(request, 'registry/churches/form.html', {
        'form': form,
        'title': 'Edit Church',
        'church': church
    })


@admin_required
def church_delete(request, pk):
    church = get_object_or_404(Church, pk=pk)
    if request.method == 'POST':
        church_name = church.name
        church.delete()
        messages.success(request, f'Church "{church_name}" has been deleted.')
        return redirect('church_list')
    return render(request, 'registry/churches/confirm_delete.html', {
        'church': church
    })


@admin_required
def parish_list(request):
    q = request.GET.get('q', '')
    church_filter = request.GET.get('church_filter', '')
    
    parishes = Parish.objects.all()
    
    if q:
        parishes = parishes.filter(
            Q(name__icontains=q) |
            Q(location__icontains=q)
        )
    
    if church_filter:
        parishes = parishes.filter(church_id=church_filter)
    
    paginator = Paginator(parishes, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'parishes': page_obj,
        'page_obj': page_obj,
        'q': q,
        'church_filter': church_filter,
        'total_parishes': Parish.objects.count(),
        'active_parishes': Parish.objects.filter(is_active=True).count(),
        'total_churches': Church.objects.count(),
        'churches': Church.objects.filter(is_active=True),
    }
    
    return render(request, 'registry/parishes/list.html', context)


@admin_required
def parish_create(request):
    """Create a new parish with church selection from dropdown"""
    if request.method == 'POST':
        form = ParishForm(request.POST)
        if form.is_valid():
            parish = form.save(commit=False)
            parish.save()
            messages.success(request, f'Parish "{parish.name}" created successfully.')
            return redirect('parish_detail', pk=parish.pk)
        else:
            # Print errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
    else:
        form = ParishForm()
        # Pre-select church if church_id is passed in GET
        if request.GET.get('church_id'):
            selected_church_id = request.GET.get('church_id')
        else:
            selected_church_id = None
    
    # Get all churches for dropdown
    churches = Church.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'registry/parishes/form.html', {
        'form': form,
        'churches': churches,
        'selected_church_id': request.GET.get('church_id', ''),
        'title': 'Add New Parish'
    })

@admin_required
def parish_detail(request, pk):
    parish = get_object_or_404(Parish, pk=pk)
    
    # Get officers
    officers = parish.parish_officers.filter(is_active=True)
    
    # Get all priests assigned to this parish (no status filter)
    priests = parish.priests.all()  # This will get all priests assigned to this parish
    
    # Filter parameters
    officer_position = request.GET.get('officer_position', '')
    
    if officer_position:
        officers = officers.filter(position=officer_position)
    
    return render(request, 'registry/parishes/detail.html', {
        'parish': parish,
        'officers': officers,
        'priests': priests,
        'officer_position': officer_position,
    })


@admin_required
def parish_edit(request, pk):
    parish = get_object_or_404(Parish, pk=pk)
    form = ParishForm(request.POST or None, instance=parish)
    if form.is_valid():
        form.save()
        messages.success(request, 'Parish updated successfully.')
        return redirect('parish_detail', pk=parish.pk)
    
    # Get all churches for dropdown
    churches = Church.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'registry/parishes/form.html', {
        'form': form,
        'churches': churches,
        'selected_church_id': str(parish.church_id) if parish.church_id else '',
        'title': f'Edit {parish.name}',
        'parish': parish
    })


@admin_required
def parish_delete(request, pk):
    parish = get_object_or_404(Parish, pk=pk)
    if request.method == 'POST':
        parish_name = parish.name
        parish.delete()
        messages.success(request, f'Parish "{parish_name}" has been deleted.')
        return redirect('parish_list')
    return render(request, 'registry/parishes/confirm_delete.html', {
        'parish': parish
    })


@admin_required
def parish_officer_add(request, parish_pk):
    parish = get_object_or_404(Parish, pk=parish_pk)
    form = ParishOfficerEPForm(request.POST or None)
    
    if form.is_valid():
        officer = form.save(commit=False)
        officer.parish = parish
        officer.save()
        messages.success(request, f'{officer.full_name} has been added as {officer.get_position_display()} to {parish.name}.')
        return redirect('parish_detail', pk=parish.pk)
    
    return render(request, 'registry/parishes/officer_form.html', {
        'form': form,
        'parish': parish,
        'title': f'Add Officer to {parish.name}'
    })


@admin_required
def parish_officer_edit(request, pk):
    officer = get_object_or_404(ParishOfficerEP, pk=pk)
    form = ParishOfficerEPForm(request.POST or None, instance=officer)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Officer information updated successfully.')
        return redirect('parish_detail', pk=officer.parish.pk)
    
    return render(request, 'registry/parishes/officer_form.html', {
        'form': form,
        'officer': officer,
        'parish': officer.parish,
        'title': 'Edit Officer'
    })


@admin_required
def parish_officer_delete(request, pk):
    officer = get_object_or_404(ParishOfficerEP, pk=pk)
    parish_pk = officer.parish.pk
    
    if request.method == 'POST':
        officer.delete()
        messages.success(request, 'Officer has been removed.')
        return redirect('parish_detail', pk=parish_pk)
    
    return render(request, 'registry/parishes/confirm_officer_delete.html', {
        'officer': officer
    })

@admin_required
def get_parishes_by_church(request, church_id):
    """API endpoint to get parishes for a specific church"""
    try:
        parishes = Parish.objects.filter(church_id=church_id, is_active=True).values('id', 'name')
        return JsonResponse({'parishes': list(parishes)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@admin_required
def get_all_parishes(request):
    """API endpoint to get all parishes"""
    try:
        parishes = Parish.objects.filter(is_active=True).values('id', 'name')
        return JsonResponse({'parishes': list(parishes)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@admin_required
def parish_officer_chart(request, pk):
    """Display parish officers in an organizational chart"""
    parish = get_object_or_404(Parish, pk=pk)
    
    # Get all active officers for this parish
    officers = parish.parish_officers.filter(is_active=True)
    
    # Group officers by position
    officers_by_position = {
        'bishop': [],
        'priest': [],
        'deacon': [],
        'senior_warden': [],
        'junior_warden': [],
        'treasurer': [],
        'secretary': [],
        'vestry_member': [],
    }
    
    for officer in officers:
        position = officer.position
        if position in officers_by_position:
            officers_by_position[position].append(officer)
    
    # Calculate total officers count
    total_officers = sum(len(officers) for officers in officers_by_position.values())
    
    return render(request, 'registry/parishes/parish_officer_chart.html', {
        'parish': parish,
        'officers_by_position': officers_by_position,
        'total_officers': total_officers,
    })

@admin_required
def parish_member(request, pk):
    """Display members belonging to a specific parish"""
    parish = get_object_or_404(Parish, pk=pk)
    
    # Get members assigned to this parish
    members = Member.objects.filter(parish=parish).order_by('last_name', 'first_name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(middle_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status_filter', '')
    if status_filter == 'active':
        members = members.filter(is_active=True)
    elif status_filter == 'inactive':
        members = members.filter(is_active=False)
    
    # Calculate statistics
    total_members = members.count()
    active_members = members.filter(is_active=True).count()
    male_members = members.filter(gender='M').count()
    female_members = members.filter(gender='F').count()
    
    # Pagination
    paginator = Paginator(members, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'registry/parishes/parish_member.html', {
        'parish': parish,
        'members': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_members': total_members,
        'active_members': active_members,
        'male_members': male_members,
        'female_members': female_members,
    })

@admin_required
def parish_priest_list(request, parish_pk):
    """Display list of priests assigned to a specific parish"""
    # Get the parish
    parish = get_object_or_404(Parish, pk=parish_pk)
    
    # Get all priests where parish field equals this parish
    priests = ParishPriest.objects.filter(parish=parish)
    
    return render(request, 'registry/parishes/parish_priest_list.html', {
        'parish': parish,
        'priests': priests,
    })

@admin_required
def priest_remove_from_parish(request, pk):
    """Remove a priest from their current parish assignment"""
    priest = get_object_or_404(ParishPriest, pk=pk)
    parish_pk = priest.parish.pk if priest.parish else None
    
    if request.method == 'POST':
        priest_name = priest.full_name
        priest.parish = None
        priest.date_assigned = None
        priest.save()
        messages.success(request, f'Rev. {priest_name} has been removed from the parish.')
        
        if parish_pk:
            return redirect('parish_priest_list', parish_pk=parish_pk)
        return redirect('priests_list')
    
    return redirect('priests_list')

@admin_required
def cathedral_list(request):
    """Display list of all cathedrals in table format"""
    from django.core.paginator import Paginator
    
    q = request.GET.get('q', '')
    church_filter = request.GET.get('church_filter', '')
    
    cathedrals = Cathedral.objects.select_related('church').all()
    
    # Search functionality
    if q:
        cathedrals = cathedrals.filter(
            Q(name__icontains=q) |
            Q(location__icontains=q) |
            Q(church__name__icontains=q)
        )
    
    # Filter by church
    if church_filter:
        cathedrals = cathedrals.filter(church_id=church_filter)
    
    # Get filter name for display
    church_filter_name = None
    if church_filter:
        try:
            church_filter_name = Church.objects.get(id=church_filter).name
        except Church.DoesNotExist:
            pass
    
    # Get all churches for filter dropdown
    churches = Church.objects.filter(is_active=True).order_by('name')
    
    # Pagination
    paginator = Paginator(cathedrals, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'cathedrals': page_obj,
        'page_obj': page_obj,
        'q': q,
        'church_filter': church_filter,
        'church_filter_name': church_filter_name,
        'churches': churches,
    }
    
    return render(request, 'registry/cathedrals/list.html', context)


@admin_required
def cathedral_detail(request, pk):
    """Display details of a specific cathedral"""
    cathedral = get_object_or_404(Cathedral, pk=pk)
    
    return render(request, 'registry/cathedrals/detail.html', {
        'cathedral': cathedral,
    })


@admin_required
def cathedral_create(request):
    """Create a new cathedral - only for churches without a cathedral"""
    if request.method == 'POST':
        form = CathedralForm(request.POST)
        if form.is_valid():
            cathedral = form.save()
            messages.success(request, f'Cathedral "{cathedral.name}" created successfully.')
            return redirect('cathedral_detail', pk=cathedral.pk)
        else:
            # Print errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
    else:
        form = CathedralForm()
        # Pre-select church if church_id is passed in GET
        if request.GET.get('church_id'):
            church_id = request.GET.get('church_id')
            try:
                church = Church.objects.get(pk=church_id)
                # Check if this church already has a cathedral
                if hasattr(church, 'cathedral'):
                    messages.error(request, f'{church.name} already has a cathedral.')
                    return redirect('church_detail', pk=church.pk)
            except Church.DoesNotExist:
                pass
    
    # Get churches without cathedral for the form (already filtered in form __init__)
    churches_without_cathedral = Church.objects.filter(
        is_active=True
    ).exclude(
        id__in=Cathedral.objects.values_list('church_id', flat=True)
    ).order_by('name')
    
    return render(request, 'registry/cathedrals/form.html', {
        'form': form,
        'churches_without_cathedral': churches_without_cathedral,
        'selected_church_id': request.GET.get('church_id', ''),
        'title': 'Add New Cathedral'
    })


@admin_required
def cathedral_edit(request, pk):
    """Edit an existing cathedral"""
    cathedral = get_object_or_404(Cathedral, pk=pk)
    original_church = cathedral.church
    
    if request.method == 'POST':
        form = CathedralForm(request.POST, instance=cathedral)
        if form.is_valid():
            updated_cathedral = form.save()
            messages.success(request, f'Cathedral "{updated_cathedral.name}" updated successfully.')
            return redirect('cathedral_detail', pk=cathedral.pk)
        else:
            # Print errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
    else:
        form = CathedralForm(instance=cathedral)
    
    return render(request, 'registry/cathedrals/form.html', {
        'form': form,
        'cathedral': cathedral,
        'title': f'Edit {cathedral.name}'
    })


@admin_required
def cathedral_delete(request, pk):
    """Delete a cathedral"""
    cathedral = get_object_or_404(Cathedral, pk=pk)
    
    if request.method == 'POST':
        cathedral_name = cathedral.name
        church_pk = cathedral.church.pk
        cathedral.delete()
        messages.success(request, f'Cathedral "{cathedral_name}" has been deleted.')
        return redirect('church_detail', pk=church_pk)
    
    return render(request, 'registry/cathedrals/confirm_delete.html', {
        'cathedral': cathedral
    })