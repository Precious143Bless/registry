from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment
from .forms import (MemberForm, BaptismForm, ConfirmationForm, CommunionForm,
                    MarriageForm, LastRitesForm, PledgeForm, PledgePaymentForm)


# ─── AUTH ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
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
    total_members = Member.objects.filter(is_active=True).count()
    total_baptisms = Baptism.objects.count()
    total_confirmations = Confirmation.objects.count()
    total_communions = FirstHolyCommunion.objects.count()
    total_marriages = Marriage.objects.count()
    total_last_rites = LastRites.objects.count()
    total_pledges = Pledge.objects.count()
    outstanding_pledges = Pledge.objects.filter(status__in=['unpaid', 'partial']).count()
    recent_members = Member.objects.filter(is_active=True).order_by('-date_registered')[:5]

    context = {
        'total_members': total_members,
        'total_baptisms': total_baptisms,
        'total_confirmations': total_confirmations,
        'total_communions': total_communions,
        'total_marriages': total_marriages,
        'total_last_rites': total_last_rites,
        'total_pledges': total_pledges,
        'outstanding_pledges': outstanding_pledges,
        'recent_members': recent_members,
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

@login_required
def sacrament_list(request):
    q = request.GET.get('q', '')
    baptisms = Baptism.objects.select_related('member')
    confirmations = Confirmation.objects.select_related('member')
    communions = FirstHolyCommunion.objects.select_related('member')
    marriages = Marriage.objects.select_related('member')
    last_rites = LastRites.objects.select_related('member')
    if q:
        baptisms = baptisms.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q))
        confirmations = confirmations.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q))
        communions = communions.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q))
        marriages = marriages.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(spouse_name__icontains=q))
        last_rites = last_rites.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q))
    context = {
        'baptisms': baptisms, 'confirmations': confirmations,
        'communions': communions, 'marriages': marriages,
        'last_rites': last_rites, 'q': q,
        'all_members': Member.objects.filter(is_active=True).order_by('last_name', 'first_name'),
    }
    return render(request, 'registry/sacraments/list.html', context)


# Baptism
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
    baptism = get_object_or_404(Baptism, pk=pk)
    return render(request, 'registry/sacraments/print_baptism.html', {'baptism': baptism})


# Confirmation
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
    return render(request, 'registry/sacraments/print_confirmation.html', {'conf': conf})


# First Holy Communion
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
    return render(request, 'registry/sacraments/print_communion.html', {'communion': communion})


# Marriage
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
    return render(request, 'registry/sacraments/print_marriage.html', {'marriage': marriage})


# Last Rites
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
    return render(request, 'registry/sacraments/print_last_rites.html', {'lr': lr})


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
    return render(request, 'registry/pledges/list.html', {'pledges': pledges, 'q': q})


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
    pledge = get_object_or_404(Pledge, pk=pk)
    payment_form = PledgePaymentForm()
    return render(request, 'registry/pledges/detail.html', {'pledge': pledge, 'payment_form': payment_form})


@login_required
def pledge_edit(request, pk):
    pledge = get_object_or_404(Pledge, pk=pk)
    form = PledgeForm(request.POST or None, instance=pledge)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pledge updated.')
        return redirect('pledge_detail', pk=pk)
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


# ─── PRINT VIEWS ─────────────────────────────────────────────────────────────

@login_required
def member_print(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'registry/members/print_member.html', {'member': member})


@login_required
def member_list_print(request):
    members = Member.objects.filter(is_active=True).order_by('last_name', 'first_name')
    return render(request, 'registry/members/print_member_list.html', {'members': members})


@login_required
def pledge_print(request, pk):
    pledge = get_object_or_404(Pledge, pk=pk)
    return render(request, 'registry/pledges/print_pledge.html', {'pledge': pledge})


@login_required
def pledge_list_print(request):
    pledges = Pledge.objects.select_related('member').order_by('member__last_name')
    return render(request, 'registry/pledges/print_pledge_list.html', {'pledges': pledges})
