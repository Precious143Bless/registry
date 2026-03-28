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
    
    # NEW: Church/Diocese Assignment
    church = models.ForeignKey(
        'Church', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='members',
        verbose_name='Assigned Church/Diocese'
    )
    
    # NEW: Parish Assignment
    parish = models.ForeignKey(
        'Parish', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='members',
        verbose_name='Assigned Parish'
    )

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name}".strip()

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)
    
    @property
    def church_parish_display(self):
        """Display the member's church and parish assignment"""
        if self.parish:
            return f"{self.parish.name} ({self.parish.church.name})"
        elif self.church:
            return f"{self.church.name}"
        return "Not Assigned"


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


class ParishInfo(models.Model):
    # Basic Information (Main Church)
    parish_name = models.CharField(max_length=200)
    diocese = models.CharField(max_length=200, blank=True)
    date_established = models.DateField(null=True, blank=True)
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)

    church_logo = models.ImageField(
        upload_to='assets/images/church/',
        blank=True,
        null=True,
        verbose_name='Church Logo'
    )
    prime_bishop_name = models.CharField(max_length=200, blank=True, verbose_name='Prime Bishop Name')
    prime_bishop_details = models.TextField(blank=True, verbose_name='Prime Bishop Details')
    prime_bishop_image = models.ImageField(
        upload_to='assets/images/priests/',
        blank=True,
        null=True,
        verbose_name='Prime Bishop Image'
    )

    # Location & Address (Diocese branches may be listed separately)
    street_address = models.CharField(max_length=255, blank=True)
    barangay = models.CharField(max_length=100, blank=True)
    municipality = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Parish Info'

    def __str__(self):
        return self.parish_name


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

class ParishPriest(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    image = models.ImageField(
        upload_to='priests/', 
        blank=True, 
        null=True,
        verbose_name='Profile Image'
    )
    
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    
    # Contact Information
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Priest Details
    ordination_date = models.DateField(null=True, blank=True)
    priest_since = models.DateField(null=True, blank=True)
    
    # NEW: Church/Diocese Assignment
    church = models.ForeignKey(
        'Church', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='priests',
        verbose_name='Assigned Church/Diocese'
    )
    
    # NEW: Parish Assignment
    parish = models.ForeignKey(
        'Parish', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='priests',
        verbose_name='Assigned Parish'
    )
    
    # Assignment
    date_assigned = models.DateField(null=True, blank=True)
    date_departed = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Biography
    biography = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    # Metadata
    date_added = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = "Parish Priests"
    
    def __str__(self):
        return f"Fr. {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)
    
    @property
    def full_name_with_title(self):
        return f"Rev. Fr. {self.first_name} {self.last_name}"
    
    @property
    def assignment_display(self):
        if self.parish:
            return f"{self.parish.name} ({self.parish.church.name})"
        elif self.church:
            return f"{self.church.name}"
        return "Not Assigned"


class ParishOfficer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    POSITION_CHOICES = [
        # Main Parish Officers
        ('parish_priest', 'Parish Priest (Pastor)'),
        ('parochial_vicar', 'Parochial Vicar / Assistant Priest'),
        ('ppc_president', 'PPC President / Chairperson'),
        ('ppc_vice_president', 'PPC Vice President'),
        ('ppc_secretary', 'PPC Secretary'),
        ('ppc_treasurer', 'PPC Treasurer'),
        ('ppc_auditor', 'PPC Auditor'),
        # Parish Finance Council
        ('finance_council', 'Parish Finance Council'),
        # Ministry Leaders
        ('lector', 'Lector (Readers)'),
        ('commentator', 'Commentator'),
        ('altar_servers', 'Altar Servers'),
        ('choir', 'Choir / Music Ministry'),
        ('extraordinary_ministers', 'Extraordinary Ministers of Holy Communion'),
        ('ushers', 'Ushers / Greeters'),
        ('collectors', 'Collectors'),
        ('sacristan', 'Sacristan'),
        ('church_decorators', 'Church Decorators'),
        ('youth_ministry', 'Youth Ministry'),
        ('family_ministry', 'Family Ministry'),
        ('womens_ministry', "Women's Ministry"),
        ('mens_ministry', "Men's Ministry"),
        ('catechists', 'Catechists (Religious Teachers)'),
        # Other Parish Officers
        ('parish_secretary', 'Parish Secretary'),
        ('parish_administrator', 'Parish Administrator'),
        ('social_communications', 'Social Communications Officer'),
        ('ministry_coordinators', 'Ministry Coordinators'),
        ('religious_education', 'Religious Education Coordinator'),
    ]

    image = models.ImageField(
        upload_to='officers/',
        blank=True,
        null=True,
        verbose_name='Profile Image'
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=150, choices=POSITION_CHOICES, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date_assigned = models.DateField(null=True, blank=True)
    date_departed = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    biography = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    date_added = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Parish Officers'

    def __str__(self):
        title = 'Officer'
        return f"{title} {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('pledge_due', 'Pledge Payment Due'),
        ('pledge_overdue', 'Pledge Payment Overdue'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_pledge = models.ForeignKey(Pledge, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Organization(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meeting_schedule = models.CharField(max_length=200, blank=True)
    meeting_venue = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()


class OrganizationMembership(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('officer', 'Officer'),
        ('president', 'President'),
        ('vice_president', 'Vice President'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('auditor', 'Auditor'),
        ('coordinator', 'Coordinator'),
        ('advisor', 'Advisor'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='organization_memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')
    joined_date = models.DateField()
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    date_created = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['member', 'organization']
        ordering = ['-joined_date']
        verbose_name = 'Organization Membership'
        verbose_name_plural = 'Organization Memberships'

    def __str__(self):
        return f"{self.member.full_name} - {self.organization.name} ({self.get_role_display()})"

class Church(models.Model):
    """Episcopal Church - contains parishes"""
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300, help_text="Full address of the church")
    description = models.TextField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Church logo and bishop
    image = models.ImageField(
        upload_to='assets/images/church/',
        blank=True,
        null=True,
        verbose_name='Church Logo'
    )
    bishop = models.CharField(max_length=200, blank=True, help_text="Current bishop of the church")
    prime_bishop_name = models.CharField(max_length=200, blank=True, help_text="Prime Bishop name")
    prime_bishop_image = models.ImageField(
        upload_to='assets/images/priests/',
        blank=True,
        null=True,
        verbose_name='Prime Bishop Image'
    )

    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Church'
        verbose_name_plural = 'Churches'

    def __str__(self):
        return self.name

    @property
    def parish_count(self):
        return self.parishes.filter(is_active=True).count()

    @property
    def total_officers(self):
        total = 0
        for parish in self.parishes.filter(is_active=True):
            total += parish.officer_count
        return total


class Parish(models.Model):
    """Parish under a church"""
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='parishes')
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300, help_text="Full address of the parish")
    description = models.TextField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Parish'
        verbose_name_plural = 'Parishes'

    def __str__(self):
        return self.name
    
    @property
    def officer_count(self):
        """Get the number of active officers in this parish"""
        return self.parish_officers.filter(is_active=True).count()


class ParishOfficerEP(models.Model):
    """Officers assigned to a specific parish"""
    OFFICER_POSITIONS = [
        ('bishop', 'Bishop'),
        ('priest', 'Priest'),
        ('deacon', 'Deacon'),
        ('senior_warden', 'Senior Warden'),
        ('junior_warden', 'Junior Warden'),
        ('treasurer', 'Treasurer'),
        ('secretary', 'Secretary'),
        ('vestry_member', 'Vestry Member'),
    ]

    parish = models.ForeignKey(Parish, on_delete=models.CASCADE, related_name='parish_officers')
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=50, choices=OFFICER_POSITIONS)
    date_assigned = models.DateField()
    date_departed = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['position', 'last_name', 'first_name']
        verbose_name = 'Parish Officer'
        verbose_name_plural = 'Parish Officers'

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.full_name} - {self.get_position_display()} ({status})"

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p)