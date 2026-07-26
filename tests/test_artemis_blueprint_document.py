from pathlib import Path


def test_full_stack_blueprint_contains_requested_sections_and_controls():
    markdown = Path("CLEARGLASSINC_ARTEMIS_FULL_STACK_INTELLIGENCE_BLUEPRINT.md").read_text()
    required_sections = [
        "## System Architecture",
        "## Data and Ontology",
        "## AI and Agent Design",
        "## Self-Improvement Loop",
        "## Full-Stack Implementation",
        "## Security and Governance",
        "## Code Examples",
        "## Scenario Walkthrough",
    ]
    for section in required_sections:
        assert section in markdown

    required_controls = [
        "ClearGlassInc Artemis",
        "Gotham",
        "Foundry",
        "AIP",
        "Apollo",
        "human approval",
        "rollback",
        "Need-to-know",
        "ModelRouter",
        "safe_to_review",
        "Python Precision Implementation Contract",
        "Secret hygiene",
        "Replayability",
        "target-state architecture",
        "No model output can grant authority",
        "PENDING_HUMAN_APPROVAL",
        "RTO of 30 minutes",
        "Shadow, A/B, and Canary Experiment Design",
        "stable mission-level assignment",
        "assign_experiment",
        "champion pointer through Apollo",
    ]
    for control in required_controls:
        assert control in markdown
