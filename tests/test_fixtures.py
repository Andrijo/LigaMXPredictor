import sys
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import requests

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import fixtures as fx
from src.liguilla import simulate_tournament
from src.utils import standings

TEAMS = [f"T{i:02d}" for i in range(18)]


def match(date, home, away, home_score, away_score):
    return {
        "date": pd.Timestamp(date), "home_team": home, "away_team": away,
        "home_score": home_score, "away_score": away_score,
    }


def tournament_with_pending(*pending_pairs):
    """Torneo de 18 equipos con todos los cruces jugados excepto los indicados."""
    pending = {frozenset(pair) for pair in pending_pairs}
    rows = [
        match("2026-08-01", home, away, 1, 0)
        for home, away in combinations(TEAMS, 2)
        if frozenset((home, away)) not in pending
    ]
    return pd.DataFrame(rows)


def espn_event(date, home, away, home_score="0", away_score="0", completed=False):
    return {
        "date": date,
        "status": {"type": {"completed": completed}},
        "competitions": [{"competitors": [
            {"homeAway": "home", "team": {"displayName": home}, "score": home_score},
            {"homeAway": "away", "team": {"displayName": away}, "score": away_score},
        ]}],
    }


class FakeResponse:
    def __init__(self, events):
        self.events = events

    def raise_for_status(self):
        pass

    def json(self):
        return {"events": self.events}


class FakeSession:
    """Sirve eventos por día, como ESPN."""

    def __init__(self, by_day):
        self.by_day = by_day
        self.calls = 0

    def get(self, url, params, timeout):
        self.calls += 1
        return FakeResponse(self.by_day.get(params["dates"], []))


def use_session(monkeypatch, session):
    monkeypatch.setattr(fx.requests, "Session", lambda: session)


def test_pending_matchups_are_the_unplayed_pairs():
    tournament = tournament_with_pending(("T00", "T01"), ("T02", "T03"))
    assert fx.pending_matchups(tournament) == {frozenset(("T00", "T01")), frozenset(("T02", "T03"))}


def test_pending_matchups_ignores_liguilla_rows():
    """Una serie de liguilla repite cruces, pero no debe contar como fase regular."""
    tournament = tournament_with_pending()
    liguilla = pd.DataFrame([match("2026-12-01", "T00", "T01", 2, 2)])
    assert fx.pending_matchups(pd.concat([tournament, liguilla])) == set()


def test_pending_matchups_needs_all_teams():
    """En la jornada 1 faltan equipos y los cruces saldrían incompletos."""
    assert fx.pending_matchups(pd.DataFrame([match("2026-07-20", "T00", "T01", 1, 0)])) == set()


def test_parse_events_normalizes_names_and_scores():
    rows = fx.parse_events({"events": [
        espn_event("2026-10-31T23:00Z", "Pumas UNAM", "Guadalajara", "3", "0", completed=True),
        espn_event("2026-11-07T23:00Z", "Atlético de San Luis", "Tigres UANL"),
    ]})
    assert (rows[0]["home_team"], rows[0]["away_team"]) == ("Pumas", "Chivas")
    assert (rows[0]["home_score"], rows[0]["away_score"]) == (3, 0)
    assert (rows[1]["home_team"], rows[1]["away_team"]) == ("Atlético San Luis", "Tigres")
    assert rows[1]["home_score"] is None


def test_fetch_stops_when_all_matchups_are_found(monkeypatch):
    tournament = tournament_with_pending(("T00", "T01"))
    session = FakeSession({"20260802": [espn_event("2026-08-02T23:00Z", "T01", "T00")]})
    use_session(monkeypatch, session)

    found = fx.fetch_fixtures(tournament, fx.pending_matchups(tournament))

    assert found.loc[0, "home_team"] == "T01"
    assert session.calls == 2


def test_fetch_ignores_matchups_that_are_not_pending(monkeypatch):
    tournament = tournament_with_pending(("T00", "T01"))
    session = FakeSession({"20260801": [
        espn_event("2026-08-01T23:00Z", "T01", "T00"),
        espn_event("2026-08-01T23:00Z", "T04", "T05"),
    ]})
    use_session(monkeypatch, session)
    assert len(fx.fetch_fixtures(tournament, fx.pending_matchups(tournament))) == 1


def test_load_fixtures_makes_no_requests_when_nothing_is_pending(monkeypatch, tmp_path):
    monkeypatch.setattr(fx, "PROCESSED_DIR", tmp_path)
    session = FakeSession({})
    use_session(monkeypatch, session)
    assert fx.load_fixtures(tournament_with_pending()).empty
    assert session.calls == 0


def test_load_fixtures_uses_expired_local_copy_when_offline(monkeypatch, tmp_path):
    monkeypatch.setattr(fx, "PROCESSED_DIR", tmp_path)
    tournament = tournament_with_pending(("T00", "T01"))
    pd.DataFrame([match("2026-11-01", "T01", "T00", None, None)]).to_csv(tmp_path / fx.FIXTURES_FILENAME, index=False)

    def offline(*args):
        raise requests.ConnectionError("sin red")

    monkeypatch.setattr(fx, "fetch_fixtures", offline)
    loaded = fx.load_fixtures(tournament, max_age_hours=-1)
    assert loaded.loc[0, "home_team"] == "T01"


def test_load_fixtures_survives_unexpected_response_format(monkeypatch, tmp_path):
    """Es una API sin documentar: si cambia su formato no debe tumbar el dashboard."""
    monkeypatch.setattr(fx, "PROCESSED_DIR", tmp_path)
    tournament = tournament_with_pending(("T00", "T01"))
    use_session(monkeypatch, FakeSession({"20260801": [{"formato": "nuevo"}]}))

    fixtures = fx.load_fixtures(tournament, max_age_hours=-1)

    assert fixtures.empty
    assert fx.missing_fixtures(tournament, fixtures) == 1


def test_played_results_update_the_table_and_leave_the_schedule():
    tournament = tournament_with_pending(("T16", "T17"), ("T15", "T17"))
    fixtures = pd.DataFrame([
        match("2026-10-31", "T17", "T16", 5.0, 0.0),
        match("2026-11-07", "T15", "T17", None, None),
    ])

    updated = fx.with_played_fixtures(tournament, fixtures)

    table = standings(updated).set_index("Equipo")
    before = standings(tournament).set_index("Equipo")
    assert table.loc["T17", "Pts"] == before.loc["T17", "Pts"] + 3
    assert fx.scheduled_fixtures(fixtures)["home_team"].tolist() == ["T15"]


def rigged_tournament_model(matrix_for):
    size = 3

    def score_matrix(home, away):
        matrix = np.zeros((size, size))
        matrix[matrix_for(home, away)] = 1.0
        return matrix

    return SimpleNamespace(
        poisson_model=SimpleNamespace(score_matrix=score_matrix, max_goals=size - 1),
        check_teams=lambda *teams: None,
    )


def test_remaining_matches_can_change_who_qualifies():
    """T08 va 9° por un partido, pero gana el pendiente y entra al top 8."""
    teams = TEAMS[:10]
    rows = []
    for i, team in enumerate(teams):
        rows.extend(match("2026-08-01", team, "Relleno", 1, 0) for _ in range(10 - i))
    tournament = pd.DataFrame(rows)
    scheduled = pd.DataFrame([match("2026-11-07", "T08", "T09", None, None)])
    model = rigged_tournament_model(lambda h, a: (2, 0))
    # T07 suma 3 victorias y T08 llegaría a 2 + 1 = 3: empate en puntos, gana por diferencia
    result = simulate_tournament(model, tournament, scheduled, n_simulations=20, seed=1).set_index("Equipo")

    assert result.loc["T08", "Pts esperados"] == result.loc["T08", "Pts"] + 3
    assert result.loc["T08", "Clasifica"] == 1
    assert result.loc["T07", "Clasifica"] == 0


def test_champion_probabilities_sum_to_one():
    teams = TEAMS[:10]
    tournament = pd.DataFrame([match("2026-08-01", team, "Relleno", 1, 0) for team in teams])
    scheduled = pd.DataFrame([match("2026-11-07", "T00", "T01", None, None)])
    rng = np.random.default_rng(3)

    def varied(home, away):
        return tuple(rng.integers(0, 3, 2))

    result = simulate_tournament(rigged_tournament_model(varied), tournament, scheduled, n_simulations=50, seed=2)
    assert result["Campeón"].sum() == pytest.approx(1.0, abs=1e-3)
    assert result["Clasifica"].sum() == pytest.approx(8.0, abs=1e-3)
