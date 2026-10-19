import type { Message } from "@langchain/langgraph-sdk";
import { expect, test } from "@rstest/core";

import {
  createHumanInputOptionResponse,
  deriveHumanInputThreadState,
  extractHumanInputRequest,
} from "@/core/messages/human-input";
import { getMessageGroups } from "@/core/messages/utils";

test("research scope results use the original confirmation card and reply protocol", () => {
  const card = {
    type: "tool",
    id: "research-card:request-1",
    name: "propose_research_scope",
    tool_call_id: "proposal-1",
    content: "研究范围确认",
    artifact: {
      human_input: {
        version: 1,
        kind: "human_input_request",
        source: "ask_clarification",
        request_id: "request-1",
        input_mode: "choice_with_other",
        question: "研究范围确认：手机，预算不限，60 秒、3 次工具调用。",
        options: [
          { id: "confirm", label: "确认并开始研究", value: "确认并开始研究" },
        ],
      },
    },
  } as unknown as Message;
  const groups = getMessageGroups([card]);
  expect(groups[0]?.type).toBe("assistant:clarification");
  const request = extractHumanInputRequest(card)!;
  const response = createHumanInputOptionResponse(
    request,
    request.options![0]!,
  );
  expect(response).toMatchObject({
    request_id: "request-1",
    option_id: "confirm",
    source: "ask_clarification",
  });
  const answered = {
    type: "human",
    content: "确认并开始研究",
    additional_kwargs: { hide_from_ui: true, human_input_response: response },
  } as unknown as Message;
  const restored = deriveHumanInputThreadState([card, answered]);
  expect(restored.latestOpenRequestId).toBeNull();
  expect(restored.answeredResponses.get("request-1")).toEqual(response);
});
