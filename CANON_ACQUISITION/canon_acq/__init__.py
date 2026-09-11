"""CANON_ACQUISITION — Autonomous Engineering Source Acquisition + Corpus Builder.

Pure-stdlib P0 implementation of the 70-section acquisition spec.
Feeds the existing CANON machine model (../CANON, ../CANON_RESEARCH).

Design principle: evidence-first. No authoritative fact without a source +
evidence pointer. UNKNOWN is a first-class value; it is never upgraded to
KNOWN just because a model thinks it likely.
"""
__version__ = "0.1.0"
