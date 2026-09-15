import unicodedata
from random import SystemRandom


ROOM_CAPACITIES = (4, 3, 3, 5, 5)
PARTICIPANT_COUNT = sum(ROOM_CAPACITIES)
MAX_DRAW_ATTEMPTS = 1000

# Keep event-specific restrictions on the server, never in presentation data.
SEPARATE_PAIRS = (("kazuma-a", "shota"), ("kazuma-a", "keito"))


class DrawUnavailable(Exception):
    pass


def name_key(name):
    return unicodedata.normalize("NFKC", name).strip().casefold()


def room_layout():
    return [
        {"number": number, "name": f"部屋{number}", "capacity": capacity}
        for number, capacity in enumerate(ROOM_CAPACITIES, start=1)
    ]


def draw_rooms(participants, *, rng=None):
    """Sample uniformly from valid assignments of the validated roster."""
    if len(participants) != PARTICIPANT_COUNT or len(
        {name_key(name) for name in participants}
    ) != PARTICIPANT_COUNT:
        raise ValueError("Expected twenty distinct participants.")

    rng = rng if rng is not None else SystemRandom()
    pairs = [(name_key(first), name_key(second)) for first, second in SEPARATE_PAIRS]
    for _ in range(MAX_DRAW_ATTEMPTS):
        shuffled = list(participants)
        rng.shuffle(shuffled)
        rooms = room_layout()
        offset = 0
        for room in rooms:
            room["members"] = shuffled[offset : offset + room["capacity"]]
            offset += room["capacity"]

        # Reject the entire draw rather than swapping people, which can bias it.
        memberships = [{name_key(name) for name in room["members"]} for room in rooms]
        if all(
            not (first in members and second in members)
            for members in memberships
            for first, second in pairs
        ):
            return rooms

    raise DrawUnavailable("No assignment found within the attempt limit.")
