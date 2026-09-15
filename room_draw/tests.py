import random
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .forms import RosterForm
from .services import (
    DrawUnavailable,
    ROOM_CAPACITIES,
    SEPARATE_PAIRS,
    draw_rooms,
    name_key,
)


def sample_participants():
    return ["kazuma-a", "shota", "keito"] + [f"member-{i:02}" for i in range(17)]


class RosterFormTests(SimpleTestCase):
    def test_blank_lines_and_surrounding_whitespace_are_removed(self):
        participants = sample_participants()
        form = RosterForm({"roster": "\r\n\r\n".join(f"  {name}  " for name in participants)})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["roster"], participants)

    def test_requires_exactly_twenty_names(self):
        for participants in ([], sample_participants()[:-1], sample_participants() + ["extra"]):
            with self.subTest(count=len(participants)):
                form = RosterForm({"roster": "\n".join(participants)})
                self.assertFalse(form.is_valid())

    def test_duplicate_names_ignore_case_and_fullwidth_variants(self):
        for duplicate in ("kazuma-a", "KAZUMA-A", "ｋａｚｕｍａ－ａ"):
            participants = sample_participants()
            participants[-1] = duplicate
            with self.subTest(duplicate=duplicate):
                form = RosterForm({"roster": "\n".join(participants)})
                self.assertFalse(form.is_valid())
                self.assertIn("重複", form.errors["roster"][0])

    def test_long_names_are_rejected(self):
        participants = sample_participants()
        participants[-1] = "a" * 81
        self.assertFalse(RosterForm({"roster": "\n".join(participants)}).is_valid())

    def test_japanese_and_html_like_names_are_preserved_as_text(self):
        participants = sample_participants()
        participants[-2:] = ["青山 和馬", "<script>alert(1)</script>"]
        form = RosterForm({"roster": "\n".join(participants)})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["roster"], participants)


class PresentationAssetTests(SimpleTestCase):
    def test_public_assets_exist_and_do_not_include_private_configuration(self):
        for asset in ("room_draw/room_draw.css", "room_draw/room_draw.js"):
            with self.subTest(asset=asset):
                path = finders.find(asset)
                self.assertIsNotNone(path)
                content = Path(path).read_text(encoding="utf-8")
                for private_value in ("SEPARATE_PAIRS", "kazuma-a", "shota", "keito"):
                    self.assertNotIn(private_value, content)


class DrawTests(SimpleTestCase):
    def test_repeated_draws_keep_every_person_capacity_and_separation(self):
        participants = sample_participants()
        original = list(participants)
        for seed in range(500):
            with self.subTest(seed=seed):
                rooms = draw_rooms(participants, rng=random.Random(seed))
                self.assertEqual([len(room["members"]) for room in rooms], list(ROOM_CAPACITIES))
                self.assertCountEqual(
                    [name for room in rooms for name in room["members"]], participants
                )
                for room in rooms:
                    for first, second in SEPARATE_PAIRS:
                        self.assertFalse(first in room["members"] and second in room["members"])
        self.assertEqual(participants, original)

    def test_separation_uses_normalized_names(self):
        participants = sample_participants()
        participants[:3] = ["ＫＡＺＵＭＡ－Ａ", "Shota", "KEITO"]
        for seed in range(50):
            rooms = draw_rooms(participants, rng=random.Random(seed))
            for room in rooms:
                names = {name_key(name) for name in room["members"]}
                self.assertFalse("kazuma-a" in names and ({"shota", "keito"} & names))

    def test_shota_and_keito_can_share_a_room(self):
        participants = sample_participants()
        allowed_order = [participants[0], *participants[3:6], participants[1], participants[2], *participants[6:]]

        class FixedRandom:
            def shuffle(self, names):
                names[:] = allowed_order

        rooms = draw_rooms(participants, rng=FixedRandom())
        self.assertIn("shota", rooms[1]["members"])
        self.assertIn("keito", rooms[1]["members"])

    def test_invalid_draw_is_rejected_and_entire_roster_is_reshuffled(self):
        participants = sample_participants()
        valid_order = [participants[0], *participants[3:6], participants[1], participants[2], *participants[6:]]

        class SequencedRandom:
            calls = 0

            def shuffle(self, names):
                self.calls += 1
                names[:] = participants if self.calls == 1 else valid_order

        rng = SequencedRandom()
        draw_rooms(participants, rng=rng)
        self.assertEqual(rng.calls, 2)

    def test_unsuccessful_sampling_is_bounded_without_ignoring_rules(self):
        class NoShuffle:
            def shuffle(self, names):
                pass

        with patch("room_draw.services.MAX_DRAW_ATTEMPTS", 3):
            with self.assertRaises(DrawUnavailable):
                draw_rooms(sample_participants(), rng=NoShuffle())

    def test_invalid_roster_is_rejected_defensively(self):
        for names in (sample_participants()[:-1], ["duplicate"] * 20):
            with self.assertRaises(ValueError):
                draw_rooms(names)


class RoomDrawViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="room-draw-test")

    def setUp(self):
        self.client.force_login(self.user)
        self.roster = "\n".join(sample_participants())

    def test_all_endpoints_require_login(self):
        client = Client()
        for name, method in (("index", "get"), ("prepare", "post"), ("draw", "post")):
            with self.subTest(endpoint=name):
                response = getattr(client, method)(reverse(f"room_draw:{name}"))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_index_and_dashboard_navigation(self):
        response = self.client.get(reverse("room_draw:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "room_draw/index.html")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertNotContains(response, "kazuma-a")
        self.assertNotContains(response, "同室NG")
        self.assertContains(self.client.get(reverse("mainpages:me")), reverse("room_draw:index"))

    def test_prepare_only_returns_roster_and_does_not_draw(self):
        with patch("room_draw.views.draw_rooms") as draw:
            response = self.client.post(reverse("room_draw:prepare"), {"roster": self.roster})
        draw.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"participants": sample_participants()})

    def test_draw_returns_only_room_data_and_does_not_persist_results(self):
        before = dict(self.client.session)
        response = self.client.post(reverse("room_draw:draw"), {"roster": self.roster})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"rooms"})
        self.assertIn("no-store", response.headers["Cache-Control"])
        for room in response.json()["rooms"]:
            self.assertEqual(set(room), {"number", "name", "capacity", "members"})
        self.assertEqual(dict(self.client.session), before)

    def test_endpoints_revalidate_roster_and_only_accept_post(self):
        for endpoint in ("prepare", "draw"):
            with self.subTest(endpoint=endpoint):
                url = reverse(f"room_draw:{endpoint}")
                self.assertEqual(self.client.get(url).status_code, 405)
                for roster in ("", "only-one", "same\n" * 20):
                    response = self.client.post(url, {"roster": roster})
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(set(response.json()), {"error"})

    def test_post_requires_csrf_and_valid_token_works(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for endpoint in ("prepare", "draw"):
            self.assertEqual(client.post(reverse(f"room_draw:{endpoint}"), {"roster": self.roster}).status_code, 403)
        client.get(reverse("room_draw:index"))
        token = client.cookies["csrftoken"].value
        self.assertEqual(
            client.post(reverse("room_draw:draw"), {"roster": self.roster}, HTTP_X_CSRFTOKEN=token).status_code,
            200,
        )

    def test_failure_is_generic_without_revealing_restrictions(self):
        with patch("room_draw.views.draw_rooms", side_effect=DrawUnavailable("private details")):
            response = self.client.post(reverse("room_draw:draw"), {"roster": self.roster})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"error": "抽選できませんでした。もう一度お試しください。"})
