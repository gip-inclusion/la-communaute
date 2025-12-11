import pytest

from lacommunaute.forum.factories import ForumFactory
from lacommunaute.partner.factories import PartnerFactory
from lacommunaute.users.factories import StaffUserFactory, UserFactory
from lacommunaute.utils.testing import parse_response_to_soup


@pytest.mark.parametrize(
    "user_factory,snapshot_name",
    [
        (lambda: None, "partner_detailview as anonymous"),
        (UserFactory, "partner_detailview"),
        (StaffUserFactory, "partner_detailview as superuser"),
    ],
)
def test_partner_detailview(client, db, snapshot, user_factory, snapshot_name):
    partner = PartnerFactory(for_snapshot=True, with_logo=True)
    user = user_factory()
    if user:
        client.force_login(user)
    response = client.get(partner.get_absolute_url())
    assert response.status_code == 200
    assert str(
        parse_response_to_soup(response, selector="main", replace_img_src=True, replace_in_href=[partner])
    ) == snapshot(name=snapshot_name)


def test_partner_with_forums(client, db, snapshot):
    partner = PartnerFactory(for_snapshot=True, with_logo=True)
    forum = ForumFactory(with_partner=partner, with_tags=["sun", "moon"], for_snapshot=True)
    response = client.get(partner.get_absolute_url())
    assert response.status_code == 200
    assert str(
        parse_response_to_soup(response, selector="main", replace_img_src=True, replace_in_href=[forum])
    ) == snapshot(name="partner_detailview_with_forums")
