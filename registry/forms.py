import re
from django.contrib.auth.models import User
from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment, ParishInfo, ParishPriest, ParishOfficer, OrganizationMembership, Organization, Church, Parish, ParishOfficerEP, Cathedral


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


def validate_email_format(value):
    """Enhanced email validation"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValidationError('Enter a valid email address.')


def validate_name_length(value, field_name='Name'):
    """Validate name length"""
    if len(value.strip()) < 2:
        raise ValidationError(f'{field_name} must be at least 2 characters long.')
    if len(value.strip()) > 100:
        raise ValidationError(f'{field_name} cannot exceed 100 characters.')


def validate_address_length(value):
    """Validate address length"""
    if len(value.strip()) < 10:
        raise ValidationError('Please enter a complete address (at least 10 characters).')
    if len(value.strip()) > 500:
        raise ValidationError('Address cannot exceed 500 characters.')

# ─── REGISTRATION FORM ─────────────────────────────────────────────────────────────

class ParishOfficerRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password (min. 8 characters)'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords don't match")
        
        # Check password length
        if password and len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email exists in ParishOfficer
            if not ParishOfficer.objects.filter(email=email).exists():
                raise ValidationError('This email is not registered as a parish officer.')
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError('An account with this email already exists. Please login instead.')
        
        return email


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
            'church': forms.Select(attrs={'class': 'form-select', 'id': 'member-church-select'}),
            'parish': forms.Select(attrs={'class': 'form-select', 'id': 'member-parish-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter church queryset
        self.fields['church'].queryset = Church.objects.filter(is_active=True).order_by('name')
        self.fields['church'].empty_label = "Select Church/Diocese"
        self.fields['church'].required = False
        
        # IMPORTANT: Allow all parishes initially for validation
        # The form must accept any valid parish ID, even if filtered in the template
        self.fields['parish'].queryset = Parish.objects.filter(is_active=True).order_by('name')
        self.fields['parish'].empty_label = "Select Parish"
        self.fields['parish'].required = False

    def clean_first_name(self):
        value = self.cleaned_data['first_name'].strip()
        if not value:
            raise ValidationError('First name is required.')
        validate_name_length(value, 'First name')
        validate_letters_only(value, 'First name')
        return value.title()

    def clean_middle_name(self):
        value = self.cleaned_data.get('middle_name', '').strip()
        if value:
            validate_name_length(value, 'Middle name')
            validate_letters_only(value, 'Middle name')
            return value.title()
        return value

    def clean_last_name(self):
        value = self.cleaned_data['last_name'].strip()
        if not value:
            raise ValidationError('Last name is required.')
        validate_name_length(value, 'Last name')
        validate_letters_only(value, 'Last name')
        return value.title()

    def clean_birthday(self):
        value = self.cleaned_data['birthday']
        if value > date.today():
            raise ValidationError('Birthday cannot be in the future.')
        if value.year < 1900:
            raise ValidationError('Please enter a valid birthday.')
        age = date.today().year - value.year
        if age > 120:
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
        validate_address_length(value)
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '').strip()
        if value:
            validate_email_format(value)
            qs = Member.objects.filter(email=value)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('A member with this email already exists.')
        return value
    
    def clean_parish(self):
        parish = self.cleaned_data.get('parish')
        church = self.cleaned_data.get('church')
        
        # If parish is selected, validate it exists
        if parish:
            # Check if parish exists in database
            if not Parish.objects.filter(id=parish.id).exists():
                raise ValidationError('Invalid parish selected.')
            
            # If church is selected, verify parish belongs to church
            if church and parish.church_id != church.id:
                raise ValidationError(f'This parish does not belong to {church.name}.')
        
        return parish
    
    def clean(self):
        cleaned_data = super().clean()
        church = cleaned_data.get('church')
        parish = cleaned_data.get('parish')
        
        # Auto-set church from parish if needed
        if parish and not church:
            cleaned_data['church'] = parish.church

        return cleaned_data


# ─── BAPTISM FORM ────────────────────────────────────────────────────────────

def _find_priest_pk(stored_name, qs):
    """Match a stored priest name string to a ParishPriest instance pk."""
    if not stored_name:
        return None
    stored = stored_name.strip().lower()
    # Strip common prefixes
    for prefix in ('rev. fr. ', 'fr. ', 'rev. ', 'rev '):
        if stored.startswith(prefix):
            stored = stored[len(prefix):]
    for p in qs:
        # Match against __str__ (Fr. First Last), full_name (First Middle Last), and first+last
        candidates = [
            str(p).lower(),
            p.full_name.lower(),
            f"{p.first_name} {p.last_name}".lower(),
        ]
        # Also strip prefixes from candidates
        stripped_candidates = []
        for c in candidates:
            for prefix in ('rev. fr. ', 'fr. ', 'rev. ', 'rev '):
                if c.startswith(prefix):
                    c = c[len(prefix):]
            stripped_candidates.append(c)
        if stored in stripped_candidates or any(stored in c or c in stored for c in stripped_candidates):
            return p.pk
    return None


def _priest_initial(stored_name, qs):
    """Return the pk of the ParishPriest matching the stored name, for ModelChoiceField initial."""
    return _find_priest_pk(stored_name, qs)


class BaptismForm(forms.ModelForm):
    date_baptized = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ParishPriest.objects.order_by('last_name', 'first_name')
        self.fields['priest'] = forms.ModelChoiceField(
            queryset=qs,
            empty_label="Select Officiating Priest",
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        # Auto-select the saved priest when editing
        if self.instance and self.instance.pk and self.instance.priest:
            priest_obj = _priest_initial(self.instance.priest, qs)
            if priest_obj:
                self.initial['priest'] = priest_obj

    class Meta:
        model = Baptism
        exclude = ['member']
        widgets = {
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
        value = self.cleaned_data['priest']
        if not value:
            raise ValidationError('Officiating priest is required.')
        return str(value)


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ParishPriest.objects.order_by('last_name', 'first_name')
        self.fields['priest'] = forms.ModelChoiceField(
            queryset=qs,
            empty_label="Select Officiating Priest",
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        # Auto-select the saved priest when editing
        if self.instance and self.instance.pk and self.instance.priest:
            priest_obj = _priest_initial(self.instance.priest, qs)
            if priest_obj:
                self.initial['priest'] = priest_obj

    class Meta:
        model = FirstHolyCommunion
        exclude = ['member']
        widgets = {
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_received(self):
        value = self.cleaned_data['date_received']
        validate_not_future(value)
        return value

    def clean_priest(self):
        value = self.cleaned_data['priest']
        if not value:
            raise ValidationError('Officiating priest is required.')
        return str(value)


# ─── MARRIAGE FORM ───────────────────────────────────────────────────────────

class MarriageForm(forms.ModelForm):
    date_married = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ParishPriest.objects.order_by('last_name', 'first_name')
        self.fields['priest'] = forms.ModelChoiceField(
            queryset=qs,
            empty_label="Select Officiating Priest",
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        # Auto-select the saved priest when editing
        if self.instance and self.instance.pk and self.instance.priest:
            priest_obj = _priest_initial(self.instance.priest, qs)
            if priest_obj:
                self.initial['priest'] = priest_obj

    class Meta:
        model = Marriage
        exclude = ['member']
        widgets = {
            'spouse_name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of spouse'}),
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
        value = self.cleaned_data['priest']
        if not value:
            raise ValidationError('Officiating priest is required.')
        return str(value)


# ─── LAST RITES FORM ─────────────────────────────────────────────────────────

class LastRitesForm(forms.ModelForm):
    date_administered = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ParishPriest.objects.order_by('last_name', 'first_name')
        self.fields['priest'] = forms.ModelChoiceField(
            queryset=qs,
            empty_label="Select Officiating Priest",
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        # Auto-select the saved priest when editing
        if self.instance and self.instance.pk and self.instance.priest:
            priest_obj = _priest_initial(self.instance.priest, qs)
            if priest_obj:
                self.initial['priest'] = priest_obj

    class Meta:
        model = LastRites
        exclude = ['member']
        widgets = {
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_administered(self):
        value = self.cleaned_data['date_administered']
        validate_not_future(value)
        return value

    def clean_priest(self):
        value = self.cleaned_data['priest']
        if not value:
            raise ValidationError('Officiating priest is required.')
        return str(value)


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


# ─── PARISH INFO FORM ────────────────────────────────────────────────────────

class ParishInfoForm(forms.ModelForm):
    date_established = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = ParishInfo
        fields = '__all__'
        widgets = {
            'parish_name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Saint Joseph Parish'}),
            'diocese':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Diocese of Cubao'}),
            'date_established': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'mission': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Main church mission statement'}),
            'vision': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Main church vision statement'}),
            'church_logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'prime_bishop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prime Bishop Full Name'}),
            'prime_bishop_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Prime Bishop details, BP info, contact, etc.'}),
            'prime_bishop_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House No., Street Name'}),
            'barangay':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barangay'}),
            'municipality':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Municipality / City'}),
            'province':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'}),
            'zip_code':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code', 'maxlength': '10'}),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '09XXXXXXXXX',
                'maxlength': '11', 'inputmode': 'numeric',
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'parish@example.com'}),
        }
        

# ─── PARISH PRIEST FORM ─────────────────────────────────────────────────────

class ParishPriestForm(forms.ModelForm):
    ordination_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    priest_since = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_assigned = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_departed = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = ParishPriest
        fields = '__all__'
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Juan'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dela Cruz'}),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09XXXXXXXXX',
                'maxlength': '11',
                'minlength': '11',
                'pattern': '09[0-9]{9}',
                'title': '11-digit PH mobile number starting with 09',
                'inputmode': 'numeric',
                'oninput': "this.value=this.value.replace(/[^0-9]/g,'').slice(0,11)",
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'church': forms.Select(attrs={'class': 'form-select', 'id': 'church-select'}),
            'parish': forms.Select(attrs={'class': 'form-select', 'id': 'parish-select'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Brief biography of the priest...'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional remarks...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter church queryset
        self.fields['church'].queryset = Church.objects.filter(is_active=True).order_by('name')
        self.fields['church'].empty_label = "Select Church/Diocese"
        
        # Show all parishes initially (for validation purposes)
        self.fields['parish'].queryset = Parish.objects.filter(is_active=True).order_by('name')
        self.fields['parish'].empty_label = "Select Parish"
        self.fields['parish'].required = False  # Make parish optional

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

    def clean_contact_number(self):
        value = self.cleaned_data.get('contact_number', '').strip()
        if value:
            validate_ph_contact(value)
        return value
    
    def clean_parish(self):
        parish = self.cleaned_data.get('parish')
        church = self.cleaned_data.get('church')
        
        # If parish is selected, validate it exists
        if parish:
            # If church is selected, verify parish belongs to church
            if church and parish.church_id != church.id:
                raise ValidationError(f'This parish does not belong to {church.name}.')
        
        return parish
    
    def clean(self):
        cleaned_data = super().clean()
        ordination_date = cleaned_data.get('ordination_date')
        priest_since = cleaned_data.get('priest_since')
        date_assigned = cleaned_data.get('date_assigned')
        date_departed = cleaned_data.get('date_departed')
        church = cleaned_data.get('church')
        parish = cleaned_data.get('parish')

        # Validation: priest_since should be on or after ordination_date
        if ordination_date and priest_since:
            if priest_since < ordination_date:
                raise ValidationError({
                    'priest_since': 'Priest since date cannot be before ordination date.'
                })

        # Validation: date_assigned should be on or after ordination_date
        if ordination_date and date_assigned:
            if date_assigned < ordination_date:
                raise ValidationError({
                    'date_assigned': 'Date assigned cannot be before ordination date.'
                })

        # Validation: date_departed should be after date_assigned
        if date_assigned and date_departed:
            if date_departed <= date_assigned:
                raise ValidationError({
                    'date_departed': 'Date departed must be after date assigned.'
                })

        # Validation: date_departed should be after ordination_date
        if ordination_date and date_departed:
            if date_departed <= ordination_date:
                raise ValidationError({
                    'date_departed': 'Date departed cannot be before or on ordination date.'
                })
        
        # Auto-set church from parish if needed
        if parish and not church:
            cleaned_data['church'] = parish.church

        return cleaned_data


# ─── PARISH OFFICER FORM ─────────────────────────────────────────────────────

class ParishOfficerForm(forms.ModelForm):
    date_assigned = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_departed = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'parish_priest' from position choices in the form
        position_choices = list(self.fields['position'].choices)
        self.fields['position'].choices = [choice for choice in position_choices if choice[0] != 'parish_priest']

    class Meta:
        model = ParishOfficer
        fields = '__all__'
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Juan'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dela Cruz'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09XXXXXXXXX',
                'maxlength': '11',
                'minlength': '11',
                'pattern': '09[0-9]{9}',
                'title': '11-digit PH mobile number starting with 09',
                'inputmode': 'numeric',
                'oninput': "this.value=this.value.replace(/[^0-9]/g,'').slice(0,11)",
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Brief biography or role details...'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional remarks...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
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

    def clean_contact_number(self):
        value = self.cleaned_data.get('contact_number', '').strip()
        if value:
            validate_ph_contact(value)
        return value


# ─── ORGANIZATION FORM ─────────────────────────────────────────────────────

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description', 'meeting_schedule', 'meeting_venue', 'contact_person', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Legion of Mary'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of the organization...'}),
            'meeting_schedule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Every Sunday, 9:00 AM'}),
            'meeting_venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Parish Hall Room 2'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Juan Dela Cruz (President)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('Organization name is required.')
        if len(name) < 3:
            raise ValidationError('Organization name must be at least 3 characters.')
        return name


# ─── ORGANIZATION MEMBERSHIP FORM ─────────────────────────────────────────

class OrganizationMembershipForm(forms.ModelForm):
    joined_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=date.today
    )

    class Meta:
        model = OrganizationMembership
        fields = ['member', 'role', 'joined_date', 'is_active', 'remarks']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active members
        self.fields['member'].queryset = Member.objects.filter(is_active=True).order_by('last_name', 'first_name')


# ─── CHURCH FORM ─────────────────────────────────────────────────────────

class ChurchForm(forms.ModelForm):
    established_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Church
        fields = ['name', 'location', 'description', 'established_date', 'contact_number', 'email', 'is_active', 'image', 'bishop']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Cathedral of St. Mary and St. John'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description...'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XXXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'church@email.com'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'bishop': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., The Rt. Rev. John Smith'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field optional
        self.fields['image'].required = False
        self.fields['image'].widget.attrs.update({'accept': 'image/*'})

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('Church name is required.')
        if len(name) < 3:
            raise ValidationError('Church name must be at least 3 characters.')
        return name

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validate file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large (max 5MB).')
            # Validate file type
            if not image.content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                raise ValidationError('Only JPEG, PNG, GIF, and WEBP images are allowed.')
        return image


# ─── PARISH FORM ─────────────────────────────────────────────────────────

class ParishForm(forms.ModelForm):
    established_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Parish
        fields = ['church', 'name', 'location', 'description', 'established_date', 'contact_number', 'email', 'is_active']
        widgets = {
            'church': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., St. Stephen\'s Parish'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description...'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XXXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'parish@email.com'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make name and location fields required
        self.fields['name'].required = True
        self.fields['location'].required = True

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('Parish name is required.')
        if len(name) < 3:
            raise ValidationError('Parish name must be at least 3 characters.')
        return name

    def clean_location(self):
        location = self.cleaned_data['location'].strip()
        if not location:
            raise ValidationError('Location is required.')
        if len(location) < 10:
            raise ValidationError('Please enter a complete address (at least 10 characters).')
        return location

    def clean_contact_number(self):
        value = self.cleaned_data.get('contact_number', '').strip()
        if value:
            if not re.match(r'^09\d{9}$', value):
                raise ValidationError('Enter a valid 11-digit Philippine mobile number starting with 09.')
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '').strip()
        if value:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValidationError('Enter a valid email address.')
        return value


# ─── PARISH OFFICER EP FORM ───────────────────────────────────────────────

class ParishOfficerEPForm(forms.ModelForm):
    date_assigned = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_departed = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = ParishOfficerEP
        fields = ['first_name', 'middle_name', 'last_name', 'position', 'date_assigned', 'date_departed', 'is_active', 'contact_number', 'email', 'remarks']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle name (optional)'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XXXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_first_name(self):
        value = self.cleaned_data['first_name'].strip()
        if not value:
            raise ValidationError('First name is required.')
        if len(value) < 2:
            raise ValidationError('First name must be at least 2 characters.')
        return value.title()

    def clean_last_name(self):
        value = self.cleaned_data['last_name'].strip()
        if not value:
            raise ValidationError('Last name is required.')
        if len(value) < 2:
            raise ValidationError('Last name must be at least 2 characters.')
        return value.title()
    
    def clean_contact_number(self):
        value = self.cleaned_data.get('contact_number', '').strip()
        if value:
            validate_ph_contact(value)
        return value
    
    def clean(self):
        cleaned_data = super().clean()
        date_assigned = cleaned_data.get('date_assigned')
        date_departed = cleaned_data.get('date_departed')
        
        if date_assigned and date_departed and date_departed <= date_assigned:
            raise ValidationError('Date departed must be after date assigned.')
        
        return cleaned_data

class CathedralForm(forms.ModelForm):
    established_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Cathedral
        fields = ['church', 'name', 'location', 'description', 'established_date', 'contact_number', 'email', 'is_active']
        widgets = {
            'church': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., St. Mary\'s Cathedral'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description...'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09XXXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'cathedral@email.com'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter churches that don't have a cathedral yet
        churches_with_cathedral = Cathedral.objects.values_list('church_id', flat=True)
        self.fields['church'].queryset = Church.objects.filter(
            is_active=True
        ).exclude(
            id__in=churches_with_cathedral
        ).order_by('name')
        self.fields['church'].empty_label = "Select Church"
        self.fields['name'].required = True
        self.fields['location'].required = True

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('Cathedral name is required.')
        if len(name) < 3:
            raise ValidationError('Cathedral name must be at least 3 characters.')
        return name

    def clean_location(self):
        location = self.cleaned_data['location'].strip()
        if not location:
            raise ValidationError('Location is required.')
        if len(location) < 10:
            raise ValidationError('Please enter a complete address (at least 10 characters).')
        return location

    def clean_contact_number(self):
        value = self.cleaned_data.get('contact_number', '').strip()
        if value:
            if not re.match(r'^09\d{9}$', value):
                raise ValidationError('Enter a valid 11-digit Philippine mobile number starting with 09.')
        return value

    def clean_email(self):
        value = self.cleaned_data.get('email', '').strip()
        if value:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValidationError('Enter a valid email address.')
        return value