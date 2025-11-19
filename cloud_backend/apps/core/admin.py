"""
Custom Django Admin Site Configuration
AgentVerse Cloud Admin Panel
"""

from django.contrib import admin
from django.contrib.admin import AdminSite


class AgentVerseAdminSite(AdminSite):
    """
    Custom admin site for AgentVerse Cloud Backend.

    This admin interface is accessible only to AgentVerse team members
    in the private network for managing the multi-tenant platform.
    """

    # Site configuration
    site_header = "AgentVerse Cloud Admin"
    site_title = "AgentVerse Admin"
    index_title = "Multi-Tenant Platform Management"

    # Branding
    site_url = None  # Disable "View site" link (private admin only)
    enable_nav_sidebar = True

    def each_context(self, request):
        """
        Add custom context to all admin pages.
        """
        context = super().each_context(request)

        # Add version info
        context['app_version'] = '1.0.0'

        # Add current tenant info (if in tenant schema)
        if hasattr(request, 'tenant'):
            context['current_tenant'] = request.tenant

        return context


# Create custom admin site instance
admin_site = AgentVerseAdminSite(name='agentverse_admin')


# Customize default admin actions
class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with common customizations for all models.
    """

    # Show 25 items per page by default
    list_per_page = 25

    # Enable search bar
    show_full_result_count = True

    # Save actions
    save_as = True
    save_as_continue = True
    save_on_top = True

    def get_actions(self, request):
        """Customize available actions"""
        actions = super().get_actions(request)

        # Remove default delete action for safety
        # (custom delete actions with confirmations can be added per model)
        if 'delete_selected' in actions:
            del actions['delete_selected']

        return actions
