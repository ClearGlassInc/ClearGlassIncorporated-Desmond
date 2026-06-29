from __future__ import annotations

from tools.artemis_self_improvement_engine import (
    ArtemisImprovementEngine,
    FeedbackSignal,
    SignalType,
)


def _correction(signal_id: str, compartment: str) -> FeedbackSignal:
    return FeedbackSignal(
        signal_id=signal_id,
        signal_type=SignalType.OPERATOR_CORRECTION,
        mission_id="m-2040",
        ontology_object_id="case-7",
        actor="analyst",
        classification="SECRET",
        compartment=compartment,
        payload={"correction": "missed_context", "theme": compartment.lower()},
    )


def test_synthesize_proposals_keeps_security_scopes_separate() -> None:
    signals = [
        _correction("a1", "ARTEMIS"),
        _correction("a2", "ARTEMIS"),
        _correction("a3", "ARTEMIS"),
        _correction("p1", "PARTNER"),
        _correction("p2", "PARTNER"),
        _correction("p3", "PARTNER"),
    ]
    engine = ArtemisImprovementEngine({"aip.agent.triage_copilot": "2.4.9"})

    proposals = engine.synthesize_proposals(signals)

    assert len(proposals) == 2
    scopes = {(proposal.classification, proposal.compartment) for proposal in proposals}
    assert scopes == {("SECRET", "ARTEMIS"), ("SECRET", "PARTNER")}

    for proposal in proposals:
        manifest = proposal.signed_manifest
        assert manifest["classification"] == proposal.classification
        assert manifest["compartment"] == proposal.compartment
        assert len(manifest["evidence_hashes"]) == 3
        assert proposal.classification in proposal.proposal_id
        assert proposal.compartment in proposal.proposal_id
