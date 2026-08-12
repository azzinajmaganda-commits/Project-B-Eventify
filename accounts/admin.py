from django.contrib import admin

from .models import AdminAccessRequest, User


# =========================================================
# HELPER
# =========================================================

def is_primary_admin(user):
    return (
        user.is_authenticated
        and user.role == User.Role.ADMIN
        and user.is_primary_admin
        and user.admin_access_status == "approved"
        and user.is_staff
        and user.is_superuser
    )


# =========================================================
# USER ADMIN
# =========================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "admin_access_status",
        "is_primary_admin",
        "is_staff",
        "is_superuser",
    )

    list_filter = (
        "role",
        "admin_access_status",
        "is_primary_admin",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    # -----------------------------------------------------
    # PRIMARY ADMIN CANNOT BE MODIFIED BY SECONDARY ADMINS
    # -----------------------------------------------------

    def has_change_permission(self, request, obj=None):
        if obj is not None:

            # Nobody except the primary admin can modify
            # the primary admin account.
            if obj.is_primary_admin:
                return is_primary_admin(request.user)

        return super().has_change_permission(request, obj)

    # -----------------------------------------------------
    # PRIMARY ADMIN CANNOT BE DELETED
    # -----------------------------------------------------

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.is_primary_admin:
            return False

        return super().has_delete_permission(request, obj)

    # -----------------------------------------------------
    # SECONDARY ADMINS CANNOT CREATE USERS AS ADMIN
    # -----------------------------------------------------

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not is_primary_admin(request.user):

            # Secondary admins cannot manipulate
            # Django's permission flags.
            if "is_staff" in form.base_fields:
                form.base_fields["is_staff"].disabled = True

            if "is_superuser" in form.base_fields:
                form.base_fields["is_superuser"].disabled = True

            if "is_primary_admin" in form.base_fields:
                form.base_fields["is_primary_admin"].disabled = True

            # Remove Admin from the role choices.
            if "role" in form.base_fields:
                form.base_fields["role"].choices = [
                    choice
                    for choice in form.base_fields["role"].choices
                    if choice[0] != User.Role.ADMIN
                ]

        return form

    # -----------------------------------------------------
    # SERVER-SIDE SECURITY
    # -----------------------------------------------------

    def save_model(self, request, obj, form, change):

        primary = is_primary_admin(request.user)

        # -------------------------------------------------
        # SECONDARY ADMIN
        # -------------------------------------------------

        if not primary:

            # A secondary admin must NEVER be able to
            # modify the primary admin.
            if obj.is_primary_admin:
                return

            # Secondary admins cannot create/promote anyone
            # to administrator.
            if obj.role == User.Role.ADMIN:

                # If this is an existing normal user,
                # preserve their previous role.
                if change:
                    old_user = User.objects.get(pk=obj.pk)
                    obj.role = old_user.role
                else:
                    obj.role = User.Role.ATTENDEE

            # Secondary admins cannot grant Django's
            # staff/superuser privileges.
            obj.is_staff = False
            obj.is_superuser = False

            # Secondary admins cannot create another
            # primary administrator.
            obj.is_primary_admin = False

        # -------------------------------------------------
        # PRIMARY ADMIN
        # -------------------------------------------------

        else:

            # Only the existing primary admin can create
            # another approved admin through controlled
            # admin-access approval.
            #
            # Even the primary admin should not accidentally
            # create another primary administrator.
            if obj.pk:
                old_user = User.objects.get(pk=obj.pk)

                if old_user.is_primary_admin:
                    obj.is_primary_admin = True

            else:
                obj.is_primary_admin = False

        super().save_model(request, obj, form, change)

    # -----------------------------------------------------
    # PREVENT PRIMARY ADMIN FROM BEING REMOVED FROM LIST
    # -----------------------------------------------------

    def get_queryset(self, request):

        queryset = super().get_queryset(request)

        # Secondary admins don't even need to see the
        # primary admin account in their user-management list.
        if not is_primary_admin(request.user):
            queryset = queryset.exclude(is_primary_admin=True)

        return queryset


# =========================================================
# ADMIN ACCESS REQUESTS
# =========================================================

@admin.register(AdminAccessRequest)
class AdminAccessRequestAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "status",
        "requested_at",
        "reviewed_by",
        "reviewed_at",
    )

    list_filter = (
        "status",
        "requested_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = (
        "requested_at",
        "reviewed_at",
        "reviewed_by",
    )

    # -----------------------------------------------------
    # ONLY PRIMARY ADMIN CAN SEE THIS SECTION
    # -----------------------------------------------------

    def has_module_permission(self, request):

        return is_primary_admin(request.user)

    # -----------------------------------------------------
    # ONLY PRIMARY ADMIN CAN VIEW REQUESTS
    # -----------------------------------------------------

    def has_view_permission(self, request, obj=None):

        return is_primary_admin(request.user)

    # -----------------------------------------------------
    # ONLY PRIMARY ADMIN CAN CHANGE REQUESTS
    # -----------------------------------------------------

    def has_change_permission(self, request, obj=None):

        return is_primary_admin(request.user)

    # -----------------------------------------------------
    # ONLY PRIMARY ADMIN CAN DELETE REQUESTS
    # -----------------------------------------------------

    def has_delete_permission(self, request, obj=None):

        return is_primary_admin(request.user)

    # -----------------------------------------------------
    # NO ONE CREATES REQUESTS FROM ADMIN PANEL
    # -----------------------------------------------------

    def has_add_permission(self, request):

        return False

    # -----------------------------------------------------
    # APPROVAL / DENIAL
    # -----------------------------------------------------

    def save_model(self, request, obj, form, change):

        # Absolute server-side protection.
        if not is_primary_admin(request.user):
            return

        obj.reviewed_by = request.user

        # -------------------------------------------------
        # APPROVED
        # -------------------------------------------------

        if obj.status == AdminAccessRequest.Status.APPROVED:

            obj.user.admin_access_status = "approved"

            # Approved secondary admin gets Django admin
            # access.
            obj.user.is_staff = True
            obj.user.is_superuser = True

            # IMPORTANT:
            # They are NOT the primary administrator.
            obj.user.is_primary_admin = False

        # -------------------------------------------------
        # DENIED
        # -------------------------------------------------

        elif obj.status == AdminAccessRequest.Status.DENIED:

            obj.user.admin_access_status = "denied"

            obj.user.is_staff = False
            obj.user.is_superuser = False

            obj.user.is_primary_admin = False

        # -------------------------------------------------
        # PENDING
        # -------------------------------------------------

        elif obj.status == AdminAccessRequest.Status.PENDING:

            obj.user.admin_access_status = "pending"

            obj.user.is_staff = False
            obj.user.is_superuser = False

            obj.user.is_primary_admin = False

        obj.user.save(
            update_fields=[
                "admin_access_status",
                "is_staff",
                "is_superuser",
                "is_primary_admin",
            ]
        )

        super().save_model(
            request,
            obj,
            form,
            change,
        )