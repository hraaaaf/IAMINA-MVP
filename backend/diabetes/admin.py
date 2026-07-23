"""
Admin configuration for monitoring patient logging activity.
"""
from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Max, Min
from django.utils import timezone

from core.models import BasePatientProfile

from .models import AISummary, DiabetesProfile, LogEntry


class BasePatientProfileInline(admin.StackedInline):
    """Inline display of base patient profile in user admin."""
    model = BasePatientProfile
    extra = 0
    can_delete = False
    readonly_fields = ['created_at', 'updated_at']


class LogEntryInline(admin.TabularInline):
    """Inline display of recent log entries for a patient."""
    model = LogEntry
    extra = 0
    readonly_fields = ['created_at', 'logged_at', 'meal_type', 'blood_sugar', 'meal_description', 'insulin_units', 'exercised', 'sleep_quality', 'stressed']
    can_delete = False
    max_num = 5
    ordering = ['-created_at']


class PatientAdmin(UserAdmin):
    """Custom admin for monitoring patient activity."""

    list_display = [
        'username',
        'first_name',
        'last_name',
        'total_logs',
        'first_log_date',
        'last_log_date',
        'logs_this_week',
        'is_active',
    ]

    list_filter = ['is_active', 'date_joined']

    inlines = [BasePatientProfileInline, LogEntryInline]

    def get_queryset(self, request):
        """Annotate with log statistics."""
        qs = super().get_queryset(request)
        qs = qs.annotate(
            total_logs=Count('log_entries'),
        )
        return qs

    def total_logs(self, obj):
        """Total number of log entries."""
        return obj.log_entries.count()
    total_logs.short_description = 'Total Logs'
    total_logs.admin_order_field = 'total_logs'

    def first_log_date(self, obj):
        """Date of first log entry."""
        first = obj.log_entries.order_by('created_at').first()
        return first.created_at.strftime('%Y-%m-%d') if first else '-'
    first_log_date.short_description = 'First Log'

    def last_log_date(self, obj):
        """Date of most recent log entry."""
        last = obj.log_entries.order_by('-created_at').first()
        return last.created_at.strftime('%Y-%m-%d') if last else '-'
    last_log_date.short_description = 'Last Log'

    def logs_this_week(self, obj):
        """Number of logs in the past 7 days."""
        week_ago = timezone.now() - timedelta(days=7)
        count = obj.log_entries.filter(created_at__gte=week_ago).count()
        return count
    logs_this_week.short_description = 'Logs (7 days)'


# Unregister default User admin and register custom
admin.site.unregister(User)
admin.site.register(User, PatientAdmin)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Admin for viewing all log entries."""

    list_display = [
        'patient',
        'created_at',
        'logged_at',
        'meal_type',
        'blood_sugar',
        'insulin_units',
        'exercised',
        'sleep_quality',
        'stressed',
        'meal_preview',
    ]

    list_filter = [
        'created_at',
        'exercised',
        'sleep_quality',
        'stressed',
    ]

    search_fields = [
        'patient__username',
        'patient__first_name',
        'patient__last_name',
        'meal_description',
    ]

    readonly_fields = ['created_at']

    date_hierarchy = 'created_at'

    def meal_preview(self, obj):
        """Short preview of meal description."""
        if obj.meal_description:
            return obj.meal_description[:50] + '...' if len(obj.meal_description) > 50 else obj.meal_description
        return '-'
    meal_preview.short_description = 'Meal'


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    """Admin for AI-generated summaries."""

    list_display = [
        'patient',
        'created_at',
        'language',
        'logs_analyzed',
        'summary_preview',
    ]

    list_filter = ['language', 'created_at']

    search_fields = [
        'patient__username',
        'summary_text',
    ]

    readonly_fields = ['created_at']

    def summary_preview(self, obj):
        """Short preview of AI summary."""
        return obj.summary_text[:100] + '...' if len(obj.summary_text) > 100 else obj.summary_text
    summary_preview.short_description = 'Summary Preview'
