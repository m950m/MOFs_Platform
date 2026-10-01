"""Research-question persistence: entry, correction, history (issue #4).

One saved question, ever: the first save creates it, every later save is a
correction that appends a question_event with the previous snapshot. Blank or
whitespace wording is rejected without touching stored data. Scientific
fields left unset remain unknown (NULL) — the tool never fills their values
(plan §2; design-system rule 7).
"""

import json
import sqlite3
from dataclasses import asdict, dataclass

FIELD_NAMES = (
    "reactions",
    "material_classes",
    "conditions",
    "hard_requirements",
    "preferences",
    "meaning_of_improvement",
)


class QuestionValidationError(ValueError):
    """The proposed question cannot be saved (e.g., blank wording)."""


class QuestionPersistenceError(RuntimeError):
    """Saving failed; the previously saved question is unchanged."""


@dataclass(frozen=True)
class Question:
    wording: str
    reactions: str | None = None
    material_classes: str | None = None
    conditions: str | None = None
    hard_requirements: str | None = None
    preferences: str | None = None
    meaning_of_improvement: str | None = None
    updated_at: str | None = None


def _clean(question: Question) -> Question:
    def normalize(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    return Question(
        wording=question.wording.strip(),
        **{name: normalize(getattr(question, name)) for name in FIELD_NAMES},
    )


def save_question(conn: sqlite3.Connection, question: Question) -> Question:
    """Create or correct the single saved question; returns the saved state."""
    if question.wording is None or not question.wording.strip():
        raise QuestionValidationError(
            "Question wording is empty — enter a question before saving."
        )
    clean = _clean(question)
    previous = get_question(conn)
    action = "created" if previous is None else "corrected"
    try:
        with conn:
            if previous is None:
                conn.execute(
                    "INSERT INTO question (id, wording, reactions, material_classes, "
                    "conditions, hard_requirements, preferences, meaning_of_improvement) "
                    "VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
                    (clean.wording,)
                    + tuple(getattr(clean, name) for name in FIELD_NAMES),
                )
            else:
                conn.execute(
                    "UPDATE question SET wording = ?, reactions = ?, material_classes = ?, "
                    "conditions = ?, hard_requirements = ?, preferences = ?, "
                    "meaning_of_improvement = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = 1",
                    (clean.wording,)
                    + tuple(getattr(clean, name) for name in FIELD_NAMES),
                )
            conn.execute(
                "INSERT INTO question_event (action, previous_json, updated_json) "
                "VALUES (?, ?, ?)",
                (
                    action,
                    json.dumps(asdict(previous)) if previous is not None else None,
                    json.dumps(asdict(clean)),
                ),
            )
    except sqlite3.Error as exc:
        raise QuestionPersistenceError(
            f"Saving the question failed; the previously saved question is unchanged. ({exc})"
        ) from exc
    saved = get_question(conn)
    assert saved is not None  # we just wrote it
    return saved


def get_question(conn: sqlite3.Connection) -> Question | None:
    row = conn.execute("SELECT * FROM question WHERE id = 1").fetchone()
    if row is None:
        return None
    return Question(
        **{key: row[key] for key in ("wording", *FIELD_NAMES, "updated_at")}
    )


def count_events(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM question_event").fetchone()[0])
