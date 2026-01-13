#!/usr/bin/env python3
import os
import sys

import django
from django.db import connection


def main():
    from tests.event.factories import EventFactory
    from tests.forum.factories import CategoryForumFactory, ForumFactory
    from tests.forum_conversation.factories import AnonymousTopicFactory, PostFactory, TopicFactory
    from tests.partner.factories import PartnerFactory
    from tests.users.factories import StaffUserFactory, UserFactory

    tags = ["Pirmadienis", "Poniedziałek", "Lundi", "Montag"]

    UserFactory(
        email="super@inclusion.gouv.fr",
        username="admin",
        is_superuser=True,
        is_staff=True,
    )
    print("superuser created")
    StaffUserFactory(email="staff@inclusion.gouv.fr", username="staff")

    print("staff created")

    partners = PartnerFactory.create_batch(5, with_logo=True)
    print("partners created")

    forum = ForumFactory(name="Espace d'échanges")
    TopicFactory.create_batch(20, forum=forum, with_post=True)
    TopicFactory.create_batch(3, forum=forum, with_post=True, with_tags=tags)
    TopicFactory(forum=forum, with_post=True, with_certified_post=True)
    AnonymousTopicFactory.create_batch(2, forum=forum, with_post=True)
    PostFactory.create_batch(3, topic=TopicFactory(forum=forum, with_post=True))
    print("public forum created")

    for i in range(1, 4):
        parent = CategoryForumFactory(name=f"Thème {i}")
        TopicFactory.create_batch(2, forum=ForumFactory(parent=parent, name=f"Fiche {i}-0"), with_post=True)
        for j in range(1, 4):
            TopicFactory.create_batch(
                2,
                forum=ForumFactory(
                    parent=parent,
                    with_partner=partners[j],
                    with_tags=tags[:j],
                    name=f"Fiche {i}-{j}",
                ),
                with_post=True,
            )
    print("documentation created")

    EventFactory.create_batch(5)
    print("events created")

    # refresh materialized view
    with connection.cursor() as cursor:
        cursor.execute("REFRESH MATERIALIZED VIEW search_commonindex")
    print("search index refreshed")
    print("that's all folks!")


if __name__ == "__main__":
    sys.path.insert(0, ".")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

    django.setup()
    main()
