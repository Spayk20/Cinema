from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from cinemaapp.models import MyUser, CinemaHall, Session, Ticket


def change_status(modeladmin, request, queryset):
    for obj in queryset:
        obj.is_staff = not obj.is_staff
    MyUser.objects.bulk_update(queryset, ['is_staff'])


class MyUserAdmin(UserAdmin):
    empty_value_display = 'None'
    actions = [change_status]
    fieldsets = (
        ('Profile', {'fields': ('username', 'password', 'total_price')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'total_price'),
        }),
    )


class CinemaHallAdmin(admin.ModelAdmin):
    fields = ('name', 'size')
    search_fields = ('name',)
    list_display = ('name', 'size')


class SessionAdmin(admin.ModelAdmin):

    search_fields = ('price',)
    list_display = ('hall', 'get_show_date', 'price', 'status')
    list_filter = ('status',)


class TicketAdmin(admin.ModelAdmin):
    list_display = ('customer', 'session', 'quantity')


admin.site.register(MyUser, MyUserAdmin)
admin.site.register(CinemaHall, CinemaHallAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Ticket, TicketAdmin)