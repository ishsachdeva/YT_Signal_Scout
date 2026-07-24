"""Public deterministic Opportunity Candidate contracts."""

from app.services.opportunity_candidate.canonicalizer import (
    OpportunityCandidateCanonicalizer,
)
from app.services.opportunity_candidate.models import (
    OPPORTUNITY_CANDIDATE_SCHEMA_VERSION,
    CandidateSourcePlatform,
    OpportunityCandidate,
)

__all__ = [
    "OPPORTUNITY_CANDIDATE_SCHEMA_VERSION",
    "CandidateSourcePlatform",
    "OpportunityCandidate",
    "OpportunityCandidateCanonicalizer",
]
