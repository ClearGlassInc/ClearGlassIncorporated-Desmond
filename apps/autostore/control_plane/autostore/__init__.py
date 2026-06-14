"""PERCIVAL Autostore control plane.

Owns policy evaluation, risk scoring, approval routing, reconciliation
against source-of-truth data, and the audit ledger.  The AI may *recommend*;
only the control plane can *authorize*.
"""
__all__ = ["models", "store", "policy", "engine", "audit"]
