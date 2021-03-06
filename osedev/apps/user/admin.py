#  Copyright (C) 2017 The OSEDev Authors.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import timedelta, date
from django.contrib import admin
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
from django.db.models.aggregates import Count, Sum, Max
from django.db.models.functions import Coalesce
from .models import User, Position, UserPosition, Term
from allauth_extras.admin import BaseUserAdmin, BaseUserChangeForm

EXTRA_PERSONAL_FIELDS = 'location', 'latitude', 'longitude'
EXTRA_STATUS_FIELDS = 'is_osedev', 'is_current'


class UserChangeForm(BaseUserChangeForm):

    def clean_location(self):
        return self.cleaned_data["location"].strip()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = form = UserChangeForm
    fieldsets = BaseUserAdmin.fieldsets
    fieldsets[1][1]['fields'] += EXTRA_PERSONAL_FIELDS
    fieldsets[2][1]['fields'] = EXTRA_STATUS_FIELDS + fieldsets[2][1]['fields']
    add_fieldsets = BaseUserAdmin.add_fieldsets
    add_fieldsets[1][1]['fields'] += EXTRA_PERSONAL_FIELDS
    add_fieldsets[2][1]['fields'] = EXTRA_STATUS_FIELDS + add_fieldsets[2][1]['fields']
    readonly_fields = 'last_login', 'latitude', 'longitude'

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'hours', 'logged', 'joined',
        *EXTRA_STATUS_FIELDS, 'is_staff', 'is_active'
    )
    list_filter = ('date_joined', *EXTRA_STATUS_FIELDS, 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(minutes=Coalesce(Sum('entries__minutes'), 0))
            .annotate(last_log=Max('entries__updated'))
        )

    def hours(self, obj):
        return obj.minutes / 60
    hours.short_description = _('Hours')
    hours.admin_order_field = 'minutes'

    def joined(self, obj):
        return timesince(obj.date_joined) + ' ago'
    joined.short_description = _('Joined')
    joined.admin_order_field = 'date_joined'

    def logged(self, obj):
        if obj.last_log is None:
            return '-'
        return timesince(obj.last_log) + ' ago'
    logged.short_description = _('Last logged')
    logged.admin_order_field = 'last_log'


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    pass


class TermInline(admin.TabularInline):
    model = Term


@admin.register(UserPosition)
class UserPositionAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'term', 'terms_count')
    inlines = (TermInline,)
    fields = ('user', 'position')

    def get_readonly_fields(self, request, obj=None):
        return self.fields if obj else ((),)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        user_position = form.instance
        user_position.term = user_position.terms.order_by('-start').first()
        user_position.save()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(terms_count=Count('terms'))

    def terms_count(self, obj):
        return obj.terms_count
    terms_count.short_description = _('Terms Served')

    def add_term(self, request, queryset):
        terms_extended = 0
        for user_position in queryset:
            start_term = user_position.term
            if start_term:
                new_start = start_term.end + timedelta(days=1)
            else:
                new_start = date.today()
            new_end = new_start + timedelta(days=user_position.position.weeks * 7)
            user_position.term = Term.objects.create(
                user_position=user_position,
                start=new_start, end=new_end
            )
            user_position.save()
            terms_extended += 1
        self.message_user(request, _("{} successfully linked.").format(terms_extended))
    add_term.short_description = _("Extend selected user positions with new terms")

    actions = [add_term]
