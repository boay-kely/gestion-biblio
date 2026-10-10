from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Livre, Categorie, Emprunt, Membre, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rôle', {'fields': ('role',)}),
    )


admin.site.register(Livre)
admin.site.register(Categorie)
admin.site.register(Emprunt)
admin.site.register(Membre)
