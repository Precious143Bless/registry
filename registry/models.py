from django.db import models


class Member(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    birthday = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES)
    address = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    date_registered = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name}".strip()

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)


class Baptism(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='baptism')
    date_baptized = models.DateField()
    priest = models.CharField(max_length=150)
    godfathers = models.TextField(blank=True, default='', help_text='Comma-separated list of godfathers')
    godmothers = models.TextField(blank=True, default='', help_text='Comma-separated list of godmothers')
    birth_certificate_no = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)

    def get_godfathers(self):
        return [g.strip() for g in self.godfathers.split(',') if g.strip()]

    def get_godmothers(self):
        return [g.strip() for g in self.godmothers.split(',') if g.strip()]

    def __str__(self):
        return f"Baptism - {self.member}"


class Confirmation(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='confirmation')
    date_confirmed = models.DateField()
    bishop = models.CharField(max_length=150)
    confirmation_name = models.CharField(max_length=100)
    sponsor = models.CharField(max_length=150, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Confirmation - {self.member}"


class FirstHolyCommunion(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='communion')
    date_received = models.DateField()
    priest = models.CharField(max_length=150)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"First Holy Communion - {self.member}"


class Marriage(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='marriages')
    spouse_name = models.CharField(max_length=200)
    date_married = models.DateField()
    priest = models.CharField(max_length=150)
    principal_sponsor = models.CharField(max_length=150, blank=True)
    secondary_sponsor = models.CharField(max_length=150, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Marriage - {self.member} & {self.spouse_name}"


class LastRites(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='last_rites')
    date_administered = models.DateField()
    priest = models.CharField(max_length=150)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Last Rites - {self.member}"


class Pledge(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='pledges')
    description = models.CharField(max_length=255)
    amount_pledged = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    date_created = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.member} - {self.description}"

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance(self):
        return self.amount_pledged - self.total_paid

    def update_status(self):
        paid = self.total_paid
        if paid <= 0:
            self.status = 'unpaid'
        elif paid >= self.amount_pledged:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.save()


class PledgePayment(models.Model):
    pledge = models.ForeignKey(Pledge, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField()
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date_paid']

    def __str__(self):
        return f"Payment of {self.amount} for {self.pledge}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.pledge.update_status()
