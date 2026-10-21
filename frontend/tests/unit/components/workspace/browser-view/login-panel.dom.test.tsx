import { afterEach, expect, rs, test } from "@rstest/core";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

const { sendInput } = rs.hoisted(() => ({ sendInput: rs.fn() }));
rs.mock("@/components/workspace/browser-view/context", () => ({
  useMaybeBrowserView: () => null,
}));
rs.mock("@/components/workspace/browser-view/use-browser-stream", () => ({
  useBrowserStream: () => ({
    status: "open",
    frameUrl: "data:image/jpeg;base64,AA==",
    liveUrl: "https://example.com/",
    tabs: [
      { index: 0, title: "Shop", active: false },
      { index: 1, title: "Login popup", active: true },
    ],
    loginStatus: { remembered: false, notice: "login_required" },
    sendInput,
  }),
}));
rs.mock("@/components/workspace/browser-view/api", () => ({
  forgetBrowserLogin: rs.fn(),
  rememberBrowserLogin: rs.fn(),
  navigateBrowser: rs.fn(),
}));

import { BrowserViewPanel } from "@/components/workspace/browser-view/browser-view-panel";

afterEach(() => {
  cleanup();
  sendInput.mockReset();
});

test("switches back from an authentication popup", () => {
  render(<BrowserViewPanel threadId="thread-1" />);
  fireEvent.change(screen.getByLabelText("Browser tab"), {
    target: { value: "0" },
  });
  expect(sendInput).toHaveBeenCalledWith({ type: "activate_tab", index: 0 });
});

test("forwards pasted and composed text without keeping it in a local field", () => {
  render(<BrowserViewPanel threadId="thread-1" />);
  const input = screen.getByLabelText<HTMLTextAreaElement>(
    "Browser keyboard input",
  );
  fireEvent.paste(input, {
    clipboardData: { getData: () => "synthetic-password" },
  });
  expect(sendInput).toHaveBeenCalledWith({
    type: "text",
    text: "synthetic-password",
  });
  fireEvent.compositionStart(input);
  fireEvent.input(input, { target: { value: "中文" }, isComposing: true });
  fireEvent.compositionEnd(input, { data: "中文" });
  expect(sendInput).toHaveBeenLastCalledWith({ type: "text", text: "中文" });
  expect(input.value).toBe("");
});

test("prompts the user to sign in again without showing credentials", () => {
  render(<BrowserViewPanel threadId="thread-1" />);
  expect(screen.getByText(/sign in manually/i)).toBeTruthy();
});

test("forwards a click once and a drag without an extra click", () => {
  render(<BrowserViewPanel threadId="thread-1" />);
  const image = screen.getByRole("img");
  Object.defineProperties(image, {
    naturalWidth: { value: 800 },
    naturalHeight: { value: 600 },
    getBoundingClientRect: {
      value: () => ({ left: 0, top: 0, width: 800, height: 600 }),
    },
    setPointerCapture: { value: rs.fn() },
  });
  fireEvent.click(image, { clientX: 20, clientY: 30 });
  expect(sendInput).toHaveBeenLastCalledWith({
    type: "click",
    nx: 0.025,
    ny: 0.05,
  });
  sendInput.mockReset();
  for (const [type, clientX] of [
    ["pointerdown", 20],
    ["pointermove", 400],
    ["pointerup", 400],
  ] as const) {
    fireEvent(
      image,
      new MouseEvent(type, { bubbles: true, button: 0, clientX, clientY: 30 }),
    );
  }
  fireEvent.click(image, { clientX: 400, clientY: 30 });
  expect(sendInput.mock.calls).toEqual([
    [{ type: "down", nx: 0.025, ny: 0.05 }],
    [{ type: "move", nx: 0.5, ny: 0.05 }],
    [{ type: "up", nx: 0.5, ny: 0.05 }],
  ]);
});
