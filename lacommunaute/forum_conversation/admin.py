from django.contrib import admin
from django.db.models import Q
from machina.apps.forum_conversation.admin import PostAdmin as BasePostAdmin, TopicAdmin as BaseTopicAdmin

from lacommunaute.forum_conversation.models import CertifiedPost, Post, Topic


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
    def get_actions(self, request):
        # delete_selected action does not call delete method of the model, so Related topic is not updated.
        # When the last post of a topic is deleted, topic.posts_count remains to 1, saying ambiguous information.
        # So we remove the delete_selected action to force the user to delete posts one by one.
        return []

    list_display = (
        "__str__",
        "poster",
        "username",
        "truncated_content",
        "updated",
        "approved",
    )

    def truncated_content(self, obj):
        def truncate(s, size):
            return s[:size] + "..." if len(s) > size else s

        return truncate(str(obj.content), 64)

    list_filter = BasePostAdmin.list_filter + (
        "approved",
        UserTypePostFilter,
    )

    ordering = ["-updated"]


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
