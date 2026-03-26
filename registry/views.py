from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.management import call_command
from django.core.files.storage import default_storage
import os
import subprocess
from datetime import datetime
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment, ParishInfo, ParishPriest, ParishOfficer
from .forms import (MemberForm, BaptismForm, ConfirmationForm, CommunionForm,
                    MarriageForm, LastRitesForm, PledgeForm, PledgePaymentForm, ParishInfoForm,ParishPriestForm, ParishOfficerForm)


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
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'registry/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


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


# ─── MEMBERS ─────────────────────────────────────────────────────────────────

@login_required
def member_list(request):
    q = request.GET.get('q', '')
    members = Member.objects.filter(is_active=True)
    if q:
        members = members.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) | Q(contact_number__icontains=q)
        )
    return render(request, 'registry/members/list.html', {'members': members, 'q': q})


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


# ─── SACRAMENTS ──────────────────────────────────────────────────────────────

def _parish_ctx():
    """Helper to inject ParishInfo into print views."""
    return ParishInfo.objects.first()


@login_required
def sacrament_list(request):
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
    context = {
        'baptisms': baptisms, 'confirmations': confirmations,
        'communions': communions, 'marriages': marriages,
        'last_rites': last_rites, 'q': q,
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
    q = request.GET.get('q', '')
    pledges = Pledge.objects.select_related('member')
    if q:
        pledges = pledges.filter(
            Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) |
            Q(description__icontains=q)
        )
    return render(request, 'registry/pledges/list.html', {
        'pledges': pledges,
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
    return render(request, 'registry/pledges/form.html', {'form': form, 'title': 'Add Pledge'})


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
    form = PledgePaymentForm(request.POST or None)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.pledge = pledge
        payment.save()
        messages.success(request, 'Payment recorded.')
        return redirect('pledge_detail', pk=pledge_pk)
    return render(request, 'registry/pledges/payment_form.html', {'form': form, 'pledge': pledge})


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(PledgePayment, pk=pk)
    pledge_pk = payment.pledge.pk
    if request.method == 'POST':
        payment.delete()
        payment.pledge.update_status()
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


# ─── PARISH PRIESTS ────────────────────────────────────────────────────────────

@login_required
def priests_list(request):
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    priests = ParishPriest.objects.all()
    
    if q:
        priests = priests.filter(
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) |
            Q(email__icontains=q) |
            Q(contact_number__icontains=q)
        )
    
    if status_filter:
        priests = priests.filter(status=status_filter)
    
    return render(request, 'registry/priests/list.html', {
        'priests': priests, 
        'q': q, 
        'status_filter': status_filter
    })


@login_required
def priest_create(request):
    form = ParishPriestForm(request.POST or None, request.FILES or None) 
    if form.is_valid():
        form.save()
        messages.success(request, 'Parish priest added successfully.')
        return redirect('priests_list')
    return render(request, 'registry/priests/form.html', {
        'form': form, 
        'title': 'Add Parish Priest'
    })


@login_required
def priest_detail(request, pk):
    priest = get_object_or_404(ParishPriest, pk=pk)
    return render(request, 'registry/priests/detail.html', {'priest': priest})


@login_required
def priest_edit(request, pk):
    priest = get_object_or_404(ParishPriest, pk=pk)
    form = ParishPriestForm(request.POST or None, request.FILES or None, instance=priest) 
    if form.is_valid():
        if request.POST.get('clear_image') == 'on':
            if priest.image:
                priest.image.delete(save=False)
            form.instance.image = None
        form.save()
        messages.success(request, 'Parish priest updated successfully.')
        return redirect('priest_detail', pk=priest.pk)
    return render(request, 'registry/priests/form.html', {
        'form': form, 
        'title': 'Edit Parish Priest', 
        'priest': priest
    })


@login_required
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
    return render(request, 'registry/priests/confirm_status.html', {'priest': priest})

@login_required
def priests_list_print(request):
    priests = ParishPriest.objects.all().order_by('last_name', 'first_name')
    return render(request, 'registry/priests/print_priest_list.html', {'priests': priests})


# ─── PARISH OFFICERS ─────────────────────────────────────────────────────────

@login_required
def officers_list(request):
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    officers = ParishOfficer.objects.all()

    if q:
        officers = officers.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(middle_name__icontains=q) |
            Q(position__icontains=q) |
            Q(email__icontains=q) |
            Q(contact_number__icontains=q)
        )

    if status_filter:
        officers = officers.filter(status=status_filter)

    return render(request, 'registry/officers/list.html', {
        'officers': officers,
        'q': q,
        'status_filter': status_filter
    })


@login_required
def officer_create(request):
    form = ParishOfficerForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Parish officer added successfully.')
        return redirect('officers_list')
    return render(request, 'registry/officers/form.html', {'form': form, 'title': 'Add Parish Officer'})


@login_required
def officer_detail(request, pk):
    officer = get_object_or_404(ParishOfficer, pk=pk)
    return render(request, 'registry/officers/detail.html', {'officer': officer})


@login_required
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


@login_required
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


@login_required
def officers_list_print(request):
    officers = ParishOfficer.objects.all().order_by('last_name', 'first_name')
    return render(request, 'registry/officers/print_officer_list.html', {'officers': officers})


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


# ─── DATABASE MANAGEMENT ────────────────────────────────────────────────────────

@login_required
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


@login_required
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


# ─── PARISH INFO ─────────────────────────────────────────────────────────────

@login_required
def parish_info(request):
    info = ParishInfo.objects.first()
    if request.method == 'POST':
        form = ParishInfoForm(request.POST, instance=info)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parish information updated successfully.')
            return redirect('parish_info')
    else:
        form = ParishInfoForm(instance=info)
    return render(request, 'registry/parish_info.html', {'info': info, 'form': form})
