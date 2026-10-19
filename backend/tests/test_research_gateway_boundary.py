"""Research state is not a client-writable LangGraph input channel."""

import pytest
from fastapi import HTTPException

from app.gateway.services import normalize_input, strip_internal_context_keys, strip_server_owned_state_metadata
from deerflow.agents.research.runtime import RESEARCH_TURN_KEY


@pytest.mark.parametrize("writer", [normalize_input, strip_server_owned_state_metadata])
def test_external_state_writers_reject_research_even_when_null(writer):
    with pytest.raises(HTTPException) as error:
        writer({"research": None})
    assert error.value.status_code == 422


def test_research_turn_cannot_be_injected_through_either_config_section():
    config = {"context": {RESEARCH_TURN_KEY: {"kind": "response"}}, "configurable": {RESEARCH_TURN_KEY: {"kind": "response"}}}
    strip_internal_context_keys(config)
    assert RESEARCH_TURN_KEY not in config["context"]
    assert RESEARCH_TURN_KEY not in config["configurable"]
