"""Only confirmed, typed proposals can enter the storage tool."""
from kiki.domain.actions import ProposalState, validate_actions


def execute_confirmed(memory, proposal, now):
    if proposal.state is not ProposalState.CONFIRMED:
        raise ValueError('A proposta precisa ser confirmada antes de executar.')
    validate_actions(proposal.actions)
    return memory.apply_actions(proposal.id, proposal.actions, now)
