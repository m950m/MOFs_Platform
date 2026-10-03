"""Structure index tests (issue #24, D12 slice 1)."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import list_references
from mofs_platform.domain.structures import (
    StructureValidationError,
    capture_structure_reference,
    count_structures,
    get_structure,
    import_structure_csv,
    search_structures,
)


@pytest.fixture
def conn_with_question(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which conductive MOFs for HER and OER?"))
    return conn


@pytest.fixture
def core_csv(tmp_path):
    csv = tmp_path / "core_mof_2019.csv"
    csv.write_text(
        "MOF Name,DOI,Formula,Refcode,Extra Note\n"
        "CoCoZn(HITP)2,10.1021/acssuschemeng.5c12327,C24N12CoZn,CM-1,synthesized\n"
        "IRMOF-1,10.1002/chem.200204626,C48H24O16Zn4,CM-2,\n"
        "Unnamed-but-present,,,,\n"
    )
    return csv


def test_import_maps_flexible_headers_and_is_attributed(conn_with_question, core_csv):
    report = import_structure_csv(
        conn_with_question, core_csv, "core_mof_2019", "Mohammed (owner)"
    )
    assert report["inserted"] == 3 and report["updated"] == 0
    assert count_structures(conn_with_question, "core_mof_2019") == 3
    hits = search_structures(conn_with_question, "CoCoZn")
    assert hits[0].doi == "10.1021/acssuschemeng.5c12327"
    assert hits[0].external_id == "CM-1"
    assert hits[0].formula == "C24N12CoZn"


def test_reimport_is_idempotent_by_external_id(conn_with_question, core_csv):
    import_structure_csv(conn_with_question, core_csv, "core_mof_2019", "Mohammed (owner)")
    report = import_structure_csv(
        conn_with_question, core_csv, "core_mof_2019", "Mohammed (owner)"
    )
    assert report["updated"] == 2 and report["inserted"] == 1  # row w/o id appends
    assert count_structures(conn_with_question, "core_mof_2019") == 4


def test_import_requires_provider_contributor_and_file(conn_with_question, core_csv):
    with pytest.raises(StructureValidationError):
        import_structure_csv(conn_with_question, core_csv, "google", "Mohammed (owner)")
    with pytest.raises(StructureValidationError):
        import_structure_csv(conn_with_question, core_csv, "qmof", "")
    with pytest.raises(StructureValidationError):
        import_structure_csv(conn_with_question, "/tmp/does-not-exist.csv", "qmof", "x")


def test_import_rejects_csv_without_name_column(conn_with_question, tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("not-a-name,stuff\n1,2\n")
    with pytest.raises(StructureValidationError) as exc:
        import_structure_csv(conn_with_question, bad, "other", "x")
    assert "no column matched" in str(exc.value)


def test_search_requires_two_chars(conn_with_question, core_csv):
    import_structure_csv(conn_with_question, core_csv, "core_mof_2019", "Mohammed (owner)")
    with pytest.raises(StructureValidationError):
        search_structures(conn_with_question, "C")


def test_capture_creates_attributed_reference_with_provenance(conn_with_question, core_csv):
    import_structure_csv(conn_with_question, core_csv, "core_mof_2019", "Mohammed (owner)")
    hit = search_structures(conn_with_question, "CoCoZn")[0]
    with pytest.raises(StructureValidationError) as exc:
        capture_structure_reference(conn_with_question, hit.id, "")
    assert "who is capturing" in str(exc.value)

    record, source_id = capture_structure_reference(
        conn_with_question, hit.id, "Mohammed (owner)"
    )
    assert record.doi == "10.1021/acssuschemeng.5c12327"
    refs = list_references(conn_with_question)
    assert len(refs) == 1 and refs[0].doi == record.doi
    assert "structure index [core_mof_2019]" in refs[0].supplied_input
    assert refs[0].inspected_level == "metadata"
    # idempotent through the reference re-capture semantics
    _rec, again = capture_structure_reference(
        conn_with_question, hit.id, "Mohammed (owner)"
    )
    assert again == source_id
    assert len(list_references(conn_with_question)) == 1


def test_capture_refuses_structure_without_doi(conn_with_question, core_csv):
    import_structure_csv(conn_with_question, core_csv, "core_mof_2019", "Mohammed (owner)")
    no_doi = search_structures(conn_with_question, "Unnamed")[0]
    with pytest.raises(StructureValidationError) as exc:
        capture_structure_reference(conn_with_question, no_doi.id, "Mohammed (owner)")
    assert "no DOI in the index" in str(exc.value)


def test_unknown_structure_id_refused(conn_with_question):
    with pytest.raises(StructureValidationError):
        capture_structure_reference(conn_with_question, 999, "Mohammed (owner)")
    assert get_structure(conn_with_question, 999) is None
