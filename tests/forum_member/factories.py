import factory

from lacommunaute.forum_member.models import ForumProfile
from tests.users.factories import UserFactory


class ForumProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ForumProfile

    user = factory.SubFactory(UserFactory)
    signature = factory.Faker("sentence", nb_words=40)
