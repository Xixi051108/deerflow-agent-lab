"""JSON checkpoint state and server-authored current-turn input for research."""

from collections.abc import Mapping
from datetime import date
from typing import Literal

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict, model_validator

from deerflow.agents.human_input import read_human_input_response
from deerflow.agents.research.data import ResultRef
from deerflow.agents.research.scope import ResearchScope, ResearchScopeSession, Text
from deerflow.utils.messages import message_content_to_text

RESEARCH_TURN_KEY = "__deerflow_research_turn"
PROPOSE_SCOPE_TOOL = "propose_research_scope"
RECORD_DATA_TOOL = "record_research_data"
READ_DATA_TOOL = "read_research_data"


class ResearchState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: Text
    user_id: Text
    agent_name: Text
    session: ResearchScopeSession
    last_run_id: str | None = None
    result: ResultRef | None = None
    phase: Literal["awaiting_confirmation", "recording"] = "awaiting_confirmation"

    @model_validator(mode="before")
    @classmethod
    def derive_phase(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            session = value.get("session")
            confirmation = session.get("confirmation") if isinstance(session, dict) else getattr(session, "confirmation", None)
            value["phase"] = "recording" if confirmation is not None else "awaiting_confirmation"
        return value

    @model_validator(mode="after")
    def bind_result(self):
        if self.result is not None and (self.result.research_id, self.result.scope_version) != (self.session.research_id, self.session.scope_version):
            raise ValueError("结果索引不属于当前研究范围")
        return self


def new_research_state(*, thread_id: str, user_id: str, agent_name: str, scope: ResearchScope | None = None, as_of_date: date) -> ResearchState:
    return ResearchState(thread_id=thread_id, user_id=user_id, agent_name=agent_name, session=ResearchScopeSession(scope=scope or ResearchScope.with_defaults({}, as_of_date=as_of_date)))


def reopen_research_for_replay(value: object) -> dict:
    """A historical snapshot supplies a draft, never a reusable consent receipt."""
    research = ResearchState.model_validate(value)
    return ResearchState.model_validate({**research.model_dump(), "session": ResearchScopeSession(scope=research.session.scope), "last_run_id": None, "result": None}).model_dump(mode="json")


def extract_research_turn(graph_input: object) -> dict:
    """Read only submitted messages, never checkpoint history or caller context."""
    if not isinstance(graph_input, Mapping):
        return {"kind": "none"}
    messages = graph_input.get("messages")
    if not isinstance(messages, list):
        return {"kind": "none"}
    current = [m for m in messages if isinstance(m, HumanMessage) and (not m.additional_kwargs.get("hide_from_ui") or "human_input_response" in m.additional_kwargs)]
    if len(current) != 1:
        return {"kind": "text" if current else "none"}
    response = read_human_input_response(current[0].additional_kwargs)
    if response is not None:
        raw = current[0].additional_kwargs["human_input_response"]
        allowed = {"version", "kind", "source", "request_id", "response_kind", "value"}
        if response["response_kind"] == "option":
            allowed.add("option_id")
        if set(raw) != allowed or type(raw.get("version")) is not int:
            return {"kind": "invalid_response"}
        return {"kind": "response", "response": response, "content": message_content_to_text(current[0].content)}
    return {"kind": "text"}
