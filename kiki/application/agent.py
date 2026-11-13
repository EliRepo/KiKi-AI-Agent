"""Session-bound proposals; the LLM never creates or executes tools."""
from dataclasses import replace
import datetime as dt
import uuid

from kiki.domain.actions import ActionProposal, Clarification, ProposalState
from kiki.domain.requests import interpret_request
from kiki.application.tools import execute_confirmed


class AgentCoordinator:
    def __init__(self, memory, clock=None):
        self.memory = memory
        self.clock = clock or dt.datetime.now
        self._proposals = {}

    def prepare(self, request):
        interpreted = interpret_request(request, self.clock())
        if interpreted is None or isinstance(interpreted, Clarification):
            return interpreted
        proposal = ActionProposal(uuid.uuid4().hex, request, interpreted)
        self._proposals[proposal.id] = proposal
        return proposal

    def get(self, proposal_id):
        try:
            return self._proposals[proposal_id]
        except KeyError:
            raise ValueError('Essa proposta não pertence à sessão atual.') from None

    def cancel(self, proposal_id):
        proposal = self.get(proposal_id)
        if proposal.state is ProposalState.CANCELLED:
            return proposal
        if proposal.state is not ProposalState.PROPOSED:
            raise ValueError('Essa proposta já foi processada e não pode ser cancelada.')
        proposal = replace(proposal, state=ProposalState.CANCELLED)
        self._proposals[proposal_id] = proposal
        return proposal

    def confirm(self, proposal_id):
        proposal = self.get(proposal_id)
        if proposal.state is ProposalState.EXECUTED:
            return replace(proposal, result=replace(proposal.result, replayed=True))
        if proposal.state is not ProposalState.PROPOSED:
            raise ValueError('Essa proposta não pode ser executada. Reenvie o pedido para uma nova conferência.')
        proposal = replace(proposal, state=ProposalState.CONFIRMED)
        self._proposals[proposal_id] = proposal
        try:
            result = execute_confirmed(self.memory, proposal, self.clock())
        except Exception as error:
            proposal = replace(proposal, state=ProposalState.FAILED, error=str(error))
        else:
            proposal = replace(proposal, state=ProposalState.EXECUTED, result=result)
        self._proposals[proposal_id] = proposal
        return proposal
