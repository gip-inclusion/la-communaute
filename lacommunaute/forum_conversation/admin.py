from django.contrib import admin, messages
from django.db.models import Q
from machina.apps.forum_conversation.admin import PostAdmin as BasePostAdmin, TopicAdmin as BaseTopicAdmin

from lacommunaute.forum_conversation.models import CertifiedPost, Post, Topic
from lacommunaute.forum_moderation.models import BlockedDomainName, BlockedEmail


class UserTypePostFilter(admin.SimpleListFilter):
    title = "Type d'utilisateur"
    parameter_name = "user_type"

    def lookups(self, request, model_admin):
        return (
            ("external_user", "Utilisateur externe"),
            ("internal_user", "Utilisateur interne"),
        )

    def queryset(self, request, queryset):
        DOMAIN = "@inclusion.gouv.fr"
        conditions = Q(username__icontains=DOMAIN) | Q(poster__email__icontains=DOMAIN)
        value = self.value()
        if value == "external_user":
            return queryset.exclude(conditions).order_by("-updated")
        if value == "internal_user":
            return queryset.filter(conditions).order_by("-updated")
        return queryset


class PostAdmin(BasePostAdmin):
    list_select_related = ("poster",)
    list_display = (
        "__str__",
        "email",
        "truncated_content",
        "updated",
    )
    list_editable = []

    @admin.display(description="message")
    def truncated_content(self, obj):
        def truncate(s, size):
            return s[:size] + "..." if len(s) > size else s

        return truncate(str(obj.content), 64)

    def email(self, obj):
        return obj.username or obj.poster.email

    list_filter = BasePostAdmin.list_filter + (
        "approved",
        UserTypePostFilter,
    )

    ordering = ["-updated"]

    @admin.action(description="Supprimer les messages et bloquer les emails")
    def delete_message_and_block_email(self, request, queryset):
        emails = {post.username or post.poster.email for post in queryset}
        blocked_emails = [BlockedEmail(email=email, reason="modération message") for email in emails]
        BlockedEmail.objects.bulk_create(blocked_emails)

        queryset.delete()
        messages.success(request, "Messages supprimés et emails bloqués 👍")

    @admin.action(description="Supprimer les messages et bloquer les noms de domaine")
    def delete_message_and_block_domain_name(self, request, queryset):
        emails = {post.username or post.poster.email for post in queryset}
        domains = {email.split("@")[-1] for email in emails}
        blocked_domains = [BlockedDomainName(domain=domain, reason="modération message") for domain in domains]
        BlockedDomainName.objects.bulk_create(blocked_domains)

        queryset.delete()
        messages.success(request, "Messages supprimés et noms de domaine bloqués 👍")

    actions = [delete_message_and_block_email, delete_message_and_block_domain_name]


class PostInline(admin.StackedInline):
    model = Post
    list_display = ("__str__", "poster", "updated", "approved")
    raw_id_fields = (
        "poster",
        "topic",
    )
    extra = 0


class TopicAdmin(BaseTopicAdmin):
    raw_id_fields = (
        "poster",
        "subscribers",
    )
    inlines = [
        PostInline,
    ]
    list_filter = BaseTopicAdmin.list_filter + ("type", "approved")


class CertifiedPostAdmin(admin.ModelAdmin):
    list_display = ("topic", "post", "user")
    raw_id_fields = (
        "topic",
        "post",
        "user",
    )


admin.site.unregister(Post)
admin.site.register(Post, PostAdmin)
admin.site.unregister(Topic)
admin.site.register(Topic, TopicAdmin)
admin.site.register(CertifiedPost, CertifiedPostAdmin)
