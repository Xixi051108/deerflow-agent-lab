import { beforeEach, expect, rs, test } from "@rstest/core";

rs.mock("@/core/api/fetcher", () => ({ fetch: rs.fn() }));
rs.mock("@/core/config", () => ({ getBackendBaseURL: () => "/backend" }));

import {
  forgetBrowserLogin,
  rememberBrowserLogin,
} from "@/components/workspace/browser-view/api";
import { fetch as fetcher } from "@/core/api/fetcher";

const mockedFetch = rs.mocked(fetcher);
beforeEach(() => {
  mockedFetch.mockReset();
});

test("remembers the server browser without sending credentials from the client", async () => {
  mockedFetch.mockResolvedValueOnce(
    new Response('{"saved":true}', { status: 200 }),
  );
  await rememberBrowserLogin("thread-1");
  expect(mockedFetch).toHaveBeenCalledWith(
    "/backend/api/threads/thread-1/browser/login-state",
    { method: "PUT" },
  );
});

test("forgets saved website logins", async () => {
  mockedFetch.mockResolvedValueOnce(
    new Response('{"saved":false}', { status: 200 }),
  );
  await forgetBrowserLogin("thread-1");
  expect(mockedFetch).toHaveBeenCalledWith(
    "/backend/api/threads/thread-1/browser/login-state",
    { method: "DELETE" },
  );
});

test("shows a rejected save instead of pretending login was remembered", async () => {
  mockedFetch.mockResolvedValueOnce(
    new Response('{"detail":"Login state changed"}', { status: 409 }),
  );
  await expect(rememberBrowserLogin("thread-1")).rejects.toThrow(
    "Login state changed",
  );
});
