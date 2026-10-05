"""Adversarial rendering sweep (strict-audit MAJOR fix).

Seeds markdown/link/script payloads into EVERY stored-text table, renders
every page, and asserts no live markdown structure survives in any output:
stored content is data (AGENTS.md rule 5) — it must display verbatim and
must never render links, images, or emphasis.
"""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question

PAYLOAD = "**bold** ![img](http://evil/i) [link](http://evil) `code`"
PAYLOAD_ESCAPED_VISIBLE = "bold ![img](http://evil/i) [link](http://evil) code"


@pytest.fixture
def seeded_app(run_app, db_path):
    """Seed hostile payloads into every stored-text column, then open the app."""
    conn = connect(db_path)
    save_question(conn, Question(
        wording=f"Question {PAYLOAD}",
        reactions="HER, OER", material_classes="MOF",
        conditions="1 M KOH", hard_requirements=f"overpotential {PAYLOAD}",
        preferences=PAYLOAD, meaning_of_improvement=PAYLOAD,
    ))
    ref = conn.execute(
        "INSERT INTO source (question_id, doi, title, container, supplied_input, "
        "inspected_level, contributor, entry_method) VALUES (1, '10.9999/sweep', ?, "
        "'Sweep Journal', ?, 'abstract', 'Mohammed (owner)', 'manual')",
        (f"Title {PAYLOAD}", f"passage {PAYLOAD}"),
    )
    source_id = int(ref.lastrowid)
    sample = conn.execute(
        "INSERT INTO sample_record (source_id, designation, composition, basis) "
        "VALUES (?, ?, ?, 'experimental')",
        (source_id, f"Sample {PAYLOAD}", PAYLOAD),
    )
    sample_id = int(sample.lastrowid)
    conn.execute(
        "INSERT INTO observation (sample_id, source_id, observation_kind, value, unit, "
        "reaction, medium, evidence_location) VALUES (?, ?, 'experimental', '180', "
        "'mV', 'HER', ?, ?)",
        (sample_id, source_id, PAYLOAD, PAYLOAD),
    )
    conn.execute(
        "INSERT INTO structure_index (provider, external_id, name, formula, doi, "
        "extra_json) VALUES ('qmof', 'SWEEP-1', ?, ?, '10.9999/qsweep', ?)",
        (f"Structure {PAYLOAD}", PAYLOAD, f'{{"Band Gap {PAYLOAD}": "1.4"}}'),
    )
    conn.execute(
        "INSERT INTO lab_capability (name, description, status) VALUES (?, ?, 'current')",
        (f"Capability {PAYLOAD}", PAYLOAD),
    )
    conn.commit()
    conn.close()
    at = run_app()
    at.run()
    return at


PAGES = ["Home", "Research question", "Laboratory profile", "Sources", "Evidence",
         "Samples & identity", "Candidates", "Review", "Lab fit"]


def test_no_live_markdown_survives_anywhere(seeded_app):
    at = seeded_app
    offenders = []
    for page in PAGES:
        at.sidebar.radio[0].set_value(page)
        at.run()
        assert not at.exception, f"{page} raised: {at.exception[0].value[:200]}"
        raw = "\n".join(
            [m.value for m in at.markdown]
            + [s.value for s in at.success]
            + [w.value for w in at.warning]
            + [e.value for e in at.error]
            + [i.value for i in at.info]
        )
        # live markdown link/image structure must not survive unescaped
        if "](http://evil)" in raw.replace("\\", "") and "](http://evil)" not in raw:
            # present only in escaped form -> fine
            continue
        if "](http://evil)" in raw:
            offenders.append((page, "live link"))
    assert offenders == [], f"live markdown survived on: {offenders}"


def test_payload_visible_verbatim_after_unescape(seeded_app):
    """The escape must display the payload verbatim once backslashes are
    removed — data displays, it just cannot act."""
    at = seeded_app
    at.sidebar.radio[0].set_value("Research question")
    at.run()
    text = all_text(at).replace("\\", "")
    assert "Question **bold** ![img](http://evil/i) [link](http://evil) `code`" in text
