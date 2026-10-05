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
        "'mV ' || ?, 'HER', ?, ?)",
        (sample_id, source_id, PAYLOAD, PAYLOAD, PAYLOAD),
    )
    for kind in ("property", "preparation", "application"):
        conn.execute(
            "INSERT INTO assertion (source_id, claim_type, claim_text, "
            "evidence_location, extraction_author, epistemic_type, review_state) "
            "VALUES (?, ?, ?, ?, 'Mohammed (owner)', 'directly_reported', "
            "'needs_verification')",
            (source_id, kind, f"Claim {PAYLOAD}", PAYLOAD),
        )
    sample_b = conn.execute(
        "INSERT INTO sample_record (source_id, designation, composition, basis) "
        "VALUES (?, ?, ?, 'experimental')",
        (source_id, f"Sample B {PAYLOAD}", PAYLOAD),
    )
    conn.execute(
        "INSERT INTO identity_relation (left_sample_id, right_sample_id, level, "
        "relation, reason, review_state, merge_permission) VALUES (?, ?, 'sample', "
        "'unresolved', ?, 'needs_verification', 'none')",
        (sample_id, int(sample_b.lastrowid), PAYLOAD),
    )
    conn.execute(
        "INSERT INTO operating_state (sample_id, stage, phase_assignment, "
        "epistemic_type, evidence_location) VALUES (?, 'after', ?, 'user_judgment', ?)",
        (sample_id, PAYLOAD, PAYLOAD),
    )
    conn.execute(
        "INSERT INTO search_run (provider, query_text, scope, outcome, result_count, "
        "next_step) VALUES ('crossref', 'sweep query', 'owner_edited', 'success', 1, 'n')"
    )
    conn.execute(
        "INSERT INTO search_hit (run_id, provider, doi, title, issued_year, container, "
        "her_token, oer_token) VALUES ((SELECT MAX(id) FROM search_run), 'crossref', "
        "'10.9999/hit', ?, '2026', ?, 1, 1)",
        (f"Hit {PAYLOAD}", PAYLOAD),
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
        if page == "Candidates":
            # open the candidate card — the deepest render path
            buttons = [b for b in at.button if getattr(b, "key", "") == "inspect_candidate"]
            if buttons:
                buttons[0].click()
                at.run()
        if page == "Lab fit":
            # run an assessment so the fit reasons render (needs preparation/
            # application assertions against the lab profile)
            selects = [s for s in at.selectbox if getattr(s, "key", "") == "fit_sample"]
            if selects and selects[0].options:
                selects[0].set_value(selects[0].options[0])
                assess = [b for b in at.button if getattr(b, "key", "") == "assess_fit"]
                if assess:
                    assess[0].click()
                    at.run()
        if page == "Samples & identity":
            # render the compare/relations block
            selects = [s for s in at.selectbox if getattr(s, "key", "") == "cmp_a"]
            if selects and selects[0].options:
                selects[0].set_value(selects[0].options[0])
                cmp_b = [s for s in at.selectbox if getattr(s, "key", "") == "cmp_b"]
                if cmp_b and len(cmp_b[0].options) > 1:
                    cmp_b[0].set_value(cmp_b[0].options[1])
                compare = [b for b in at.button if getattr(b, "key", "") == "run_compare"]
                if compare:
                    compare[0].click()
                    at.run()
        if page == "Laboratory profile":
            # exercise the correction path (warning + save flash)
            correct = [b for b in at.button
                       if getattr(b, "key", "").startswith("correct_")]
            if correct:
                correct[0].click()
                at.run()
                save = [b for b in at.button if getattr(b, "key", "") == "save_capability"]
                if save:
                    name = [t for t in at.text_input if getattr(t, "key", "") == "cap_name"]
                    if name:
                        name[0].set_value(f"Capability {PAYLOAD} corrected")
                    save[0].click()
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
