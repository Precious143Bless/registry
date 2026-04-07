# User Role System Documentation

## Overview
This registry system uses a 3-tier user role system based on Django's User model:

### User Roles

1. **Admin** (`is_superuser=True`)
   - Full system access
   - Can manage all users, members, priests, and data
   - Access to Django admin interface
   - Set via Django admin only (edit User → is_superuser checkbox)

2. **Staff (Priests)** (`is_staff=True, priest_profile=ParishPriest`)
   - Registered account linked to ParishPriest record
   - Can access admin dashboard and manage parish data
   - Created automatically when a priest from the ParishPriest list registers
   - Flag enforcement: `is_staff` is automatically set to `True`

3. **Member** (`is_staff=False, member_profile=Member`)
   - Registered account linked to Member record
   - Can only access member dashboard and personal data
   - Created automatically when a member from the Member list registers
   - Flag enforcement: `is_staff` is automatically set to `False`

## User Registration Flow

### How Users Get Their Role

1. **Priest Registration:**
   - User enters name and email matching a ParishPriest record in the system
   - System automatically creates User with `is_staff=True`
   - User is linked to their ParishPriest profile
   - User gains access to admin dashboard

2. **Member Registration:**
   - User enters name and email/birthday matching a Member record in the system
   - System automatically creates User with `is_staff=False`
   - User is linked to their Member profile
   - User gains access to member dashboard only

3. **Admin Creation:**
   - Only created manually via Django admin
   - Set `is_superuser=True` to grant admin access

## Admin Interface Rules (Enforced)

### CustomUserAdmin (User Management)
The custom user admin page enforces several rules:

- **Priests must be Staff:** If a user has a priest_profile, their is_staff flag is automatically set to True
- **Members must NOT be Staff:** If a user has a member_profile, their is_staff flag is automatically set to False  
- **No Dual Roles:** A user cannot be both a priest and a member simultaneously
- **Visual Badges:** Each user shows a color-coded role badge:
  - Red: Admin
  - Blue: Staff (Priest)
  - Gray: Other Staff (should not exist)
  - Green: Member
  - Orange: No Role (account not properly configured)

### MemberAdmin
- Shows "Linked User" status
- Automatically removes is_staff=True if mistakenly set on a member's user
- Display member's assignment (Church/Parish)

### ParishPriestAdmin
- Shows "Linked User" status
- Automatically sets is_staff=True if a priest's user is missing the flag
- Displays warning if user is NOT staff (indicates configuration error)

## Important Notes

### Automatic Enforcement
The system automatically enforces role consistency:
- When saving a User that links to a priest_profile, `is_staff` is set to `True`
- When saving a User that links to a member_profile, `is_staff` is set to `False`
- This happens automatically both in registration and when editing in the admin

### Registration Requirements
Before a member or priest can register:
1. They must already exist in the Member or ParishPriest list
2. Their email must be on file OR
3. Their name and date of birth (for members) or name (for priests) must match

### Changing User Roles
To change a user's role (e.g., convert member to staff):
1. This is NOT recommended during normal operation
2. If needed, manually edit the User and create/link the appropriate profile
3. The system will auto-enforce the is_staff flag based on the profile

## Granting Admin Access

To make an existing staff member an admin:
1. Go to Django Admin → Users
2. Find the user
3. Check the "Superuser" checkbox
4. Save

To revoke admin access from a superuser:
1. Go to Django Admin → Users
2. Find the user
3. Uncheck the "Superuser" checkbox
4. Save

## Troubleshooting

### User Shows "No Role" Badge
- The user account exists but is not linked to any profile
- Solution: Link the user to either a ParishPriest or Member record
- Or delete the account and have the person register through the proper flow

### Priest Not Showing as Staff in Admin
- The priest_profile exists but is_staff is False
- Solution: The admin interface will auto-correct this on save
- Or manually check the is_staff checkbox for that user

### Member Shows as Staff
- The member_profile exists but is_staff is True
- Solution: The admin interface will auto-correct this on save
- Or manually uncheck the is_staff checkbox for that user

### Two Profiles on One User
- Very rare, but would be configuration error
- Solution: Delete the incorrect profile or unlink it from the user

## Code Implementation Details

### Admin Enforcement (admin.py)

#### CustomUserAdmin.save_model()
```python
# Priests must be staff
if is_priest and not obj.is_staff and not obj.is_superuser:
    obj.is_staff = True

# Members must NOT be staff
if is_member and obj.is_staff and not obj.is_superuser:
    obj.is_staff = False
```

#### MemberAdmin.save_model()
```python
# Remove staff flag if mistakenly set
if obj.user and obj.user.is_staff and not obj.user.is_superuser:
    obj.user.is_staff = False
    obj.user.save()
```

#### ParishPriestAdmin.save_model()
```python
# Ensure staff flag is set
if obj.user and not obj.user.is_staff and not obj.user.is_superuser:
    obj.user.is_staff = True
    obj.user.save()
```

### Registration (views.py register_view)
```python
# Priests are created as staff, members are not
is_staff = True if user_type == 'priest' else False

user = User.objects.create_user(
    username=email,
    email=email,
    password=password,
    first_name=first_name,
    last_name=last_name,
    is_active=True,
    is_staff=is_staff  # Set based on user type
)
```

## Testing the System

1. **Create a Member:**
   - Go to Admin → Members
   - Create a new member record
   - Have them register through the registration page
   - Check that their User account has is_staff=False

2. **Create a Priest:**
   - Go to Admin → Parish Priests
   - Create a new priest record
   - Have them register through the registration page
   - Check that their User account has is_staff=True

3. **Verify Admin Enforcement:**
   - Go to Admin → Users
   - Edit a member user and check is_staff
   - Manually set it to True and save
   - Reload - it should be False again (auto-corrected)
   - Repeat with a priest user and uncheck is_staff
   - Reload - it should be True again (auto-corrected)

## Summary

The role system is fully automated:
- **Priests automatically become Staff** when they register
- **Members automatically stay as Members** when they register
- **Admin creates Admins** manually
- **The admin interface enforces consistency** automatically
