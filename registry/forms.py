import re
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment


# ─── REUSABLE VALIDATORS ─────────────────────────────────────────────────────

def validate_letters_only(value, field_name='This field'):
    if not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-'.]+$", value):
        raise ValidationError(f'{field_name} must contain letters only.')


def validate_ph_contact(value):
    cleaned = re.sub(r'\s+', '', value)
    if not re.match(r'^09\d{9}$', cleaned):
        raise ValidationError(
            'Enter a valid 11-digit Philippine mobile number starting with 09 (e.g. 09171234567).'
        )


def validate_not_future(value):
    if value > date.today():
        raise ValidationError('Date cannot be in the future.')


def validate_not_past_due(value):
    if value < date.today():
        raise ValidationError('Due date cannot be in the past.')


def validate_positive_amount(value):
    if value <= 0:
        raise ValidationError('Amount must be greater than zero.')


# ─── MEMBER FORM ─────────────────────────────────────────────────────────────

class MemberForm(forms.ModelForm):
    birthday = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Format: YYYY-MM-DD'
    )

    class Meta:
        model = Member
        exclude = ['is_active', 'date_registered']
        widgets = {
            'first_name':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Juan'}),
            'middle_name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'last_name':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dela Cruz'}),
            'gender':         forms.Select(attrs={'class': 'form-select'}),
            'civil_status':   forms.Select(attrs={'class': 'form-select'}),
            'address':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'House No., Street, Barangay, City'}),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09XXXXXXXXX',
                'maxlength': '11',
                'minlength': '11',
                'pattern': '09[0-9]{9}',
                'title': '11-digit PH mobile number starting with 09',
                'inputmode': 'numeric',
                'oninput': "this.value=this.value.replace(/[^0-9]/g,'').slice(0,11)",
                'onkeypress': "return (event.charCode >= 48 && event.charCode <= 57) && this.value.length < 11",
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
        }

    def clean_first_name(self):
        value = self.cleaned_data['first_name'].strip()
        if not value:
            raise ValidationError('First name is required.')
        validate_letters_only(value, 'First name')
        return value.title()

    def clean_middle_name(self):
        value = self.cleaned_data.get('middle_name', '').strip()
        if value:
            validate_letters_only(value, 'Middle name')
            return value.title()
        return value

    def clean_last_name(self):
        value = self.cleaned_data['last_name'].strip()
        if not value:
            raise ValidationError('Last name is required.')
        validate_letters_only(value, 'Last name')
        return value.title()

    def clean_birthday(self):
        value = self.cleaned_data['birthday']
        if value > date.today():
            raise ValidationError('Birthday cannot be in the future.')
        if value.year < 1900:
            raise ValidationError('Please enter a valid birthday.')
        return value

    def clean_contact_number(self):
        value = self.cleaned_data.get('contact_number', '').strip()
        if value:
            validate_ph_contact(value)
        return value

    def clean_address(self):
        value = self.cleaned_data['address'].strip()
        if not value:
            raise ValidationError('Address is required.')
        if len(value) < 10:
            raise ValidationError('Please enter a complete address.')
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '').strip()
        if value:
            # basic duplicate check
            qs = Member.objects.filter(email=value)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('A member with this email already exists.')
        return value


# ─── BAPTISM FORM ────────────────────────────────────────────────────────────

class BaptismForm(forms.ModelForm):
    date_baptized = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Baptism
        exclude = ['member']
        widgets = {
            'priest':               forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fr. Full Name'}),
            'godfathers':           forms.HiddenInput(),
            'godmothers':           forms.HiddenInput(),
            'birth_certificate_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'remarks':              forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_baptized(self):
        value = self.cleaned_data['date_baptized']
        validate_not_future(value)
        return value

    def clean_priest(self):
        value = self.cleaned_data['priest'].strip()
        if not value:
            raise ValidationError('Officiating priest name is required.')
        return value


# ─── CONFIRMATION FORM ───────────────────────────────────────────────────────

class ConfirmationForm(forms.ModelForm):
    date_confirmed = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Confirmation
        exclude = ['member']
        widgets = {
            'bishop':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bishop Full Name'}),
            'confirmation_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Maria'}),
            'sponsor':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'remarks':           forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_confirmed(self):
        value = self.cleaned_data['date_confirmed']
        validate_not_future(value)
        return value

    def clean_bishop(self):
        value = self.cleaned_data['bishop'].strip()
        if not value:
            raise ValidationError('Officiating bishop name is required.')
        return value

    def clean_confirmation_name(self):
        value = self.cleaned_data['confirmation_name'].strip()
        if not value:
            raise ValidationError('Confirmation name is required.')
        validate_letters_only(value, 'Confirmation name')
        return value.title()


# ─── FIRST HOLY COMMUNION FORM ───────────────────────────────────────────────

class CommunionForm(forms.ModelForm):
    date_received = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = FirstHolyCommunion
        exclude = ['member']
        widgets = {
            'priest':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fr. Full Name'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_received(self):
        value = self.cleaned_data['date_received']
        validate_not_future(value)
        return value

    def clean_priest(self):
        value = self.cleaned_data['priest'].strip()
        if not value:
            raise ValidationError('Officiating priest name is required.')
        return value


# ─── MARRIAGE FORM ───────────────────────────────────────────────────────────

class MarriageForm(forms.ModelForm):
    date_married = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Marriage
        exclude = ['member']
        widgets = {
            'spouse_name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of spouse'}),
            'priest':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fr. Full Name'}),
            'principal_sponsor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'secondary_sponsor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'remarks':           forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_married(self):
        value = self.cleaned_data['date_married']
        validate_not_future(value)
        return value

    def clean_spouse_name(self):
        value = self.cleaned_data['spouse_name'].strip()
        if not value:
            raise ValidationError('Spouse name is required.')
        validate_letters_only(value, 'Spouse name')
        return value.title()

    def clean_priest(self):
        value = self.cleaned_data['priest'].strip()
        if not value:
            raise ValidationError('Officiating priest name is required.')
        return value


# ─── LAST RITES FORM ─────────────────────────────────────────────────────────

class LastRitesForm(forms.ModelForm):
    date_administered = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = LastRites
        exclude = ['member']
        widgets = {
            'priest':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fr. Full Name'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_administered(self):
        value = self.cleaned_data['date_administered']
        validate_not_future(value)
        return value

    def clean_priest(self):
        value = self.cleaned_data['priest'].strip()
        if not value:
            raise ValidationError('Officiating priest name is required.')
        return value


# ─── PLEDGE FORM ─────────────────────────────────────────────────────────────

class PledgeForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Pledge
        exclude = ['status', 'date_created']
        widgets = {
            'member':         forms.Select(attrs={'class': 'form-select'}),
            'description':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Church Renovation Fund'}),
            'amount_pledged': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1', 'placeholder': '0.00'}),
        }

    def clean_description(self):
        value = self.cleaned_data['description'].strip()
        if not value:
            raise ValidationError('Description is required.')
        if len(value) < 3:
            raise ValidationError('Description is too short.')
        return value

    def clean_amount_pledged(self):
        value = self.cleaned_data['amount_pledged']
        validate_positive_amount(value)
        return value

    def clean_due_date(self):
        value = self.cleaned_data['due_date']
        # Allow editing existing pledges without forcing future date
        if not self.instance.pk and value < date.today():
            raise ValidationError('Due date cannot be in the past.')
        return value


# ─── PLEDGE PAYMENT FORM ─────────────────────────────────────────────────────

class PledgePaymentForm(forms.ModelForm):
    date_paid = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = PledgePayment
        exclude = ['pledge']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1', 'placeholder': '0.00'}),
            'notes':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional notes'}),
        }

    def clean_amount(self):
        value = self.cleaned_data['amount']
        validate_positive_amount(value)
        return value

    def clean_date_paid(self):
        value = self.cleaned_data['date_paid']
        validate_not_future(value)
        return value
