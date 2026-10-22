import { writeFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

import {
  MOCK_THREAD_ID,
  MOCK_THREAD_ID_2,
  mockLangGraphAPI,
} from "./utils/mock-api";

// Opt in only against tests/support/browser_login_gateway.py, never a user Gateway.
test.skip(
  process.env.BROWSER_LOGIN_SYNTHETIC !== "1",
  "Requires the synthetic browser gateway",
);
test.use({ channel: process.env.PLAYWRIGHT_CHANNEL });

const streamEvents: Record<string, unknown>[] = [];
test.beforeEach(({ page }) => {
  streamEvents.length = 0;
  page.on("websocket", (socket) => {
    const record = (event: string, payload?: string | Buffer) => {
      if (typeof payload !== "string") return;
      try {
        const value = JSON.parse(payload) as {
          type?: string;
          url?: string;
          notice?: string;
        };
        streamEvents.push({
          event,
          type: value.type,
          url: value.url,
          notice: value.notice,
        });
      } catch {
        /* Binary frames are not diagnostic metadata. */
      }
    };
    streamEvents.push({ event: "created", url: socket.url() });
    socket.on("framesent", ({ payload }) => record("sent", payload));
    socket.on("framereceived", ({ payload }) => record("received", payload));
    socket.on("close", () => streamEvents.push({ event: "closed" }));
  });
});
test.afterEach(async ({ page }, testInfo) => {
  streamEvents.push({ event: "test_end", page_closed: page.isClosed() });
  const path = testInfo.outputPath("synthetic-stream-events.json");
  await writeFile(path, JSON.stringify(streamEvents, null, 2), "utf-8");
  await testInfo.attach("synthetic-browser-stream-events", {
    path,
    contentType: "application/json",
  });
});

test("panel signs in, remembers across chats, and forgets synthetic state", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(90_000);
  mockLangGraphAPI(page, {
    threads: [MOCK_THREAD_ID, MOCK_THREAD_ID_2].map((thread_id) => ({
      thread_id,
      title: "Synthetic browser login",
    })),
  });
  await page.route("**/api/threads/*/browser/**", (route) => route.continue());
  await page.goto(`/workspace/chats/${MOCK_THREAD_ID}`);
  await page.getByTestId("browser-trigger").click();
  await expect(
    page.getByRole("button", { name: "Remember login", exact: true }),
  ).toBeEnabled({ timeout: 15_000 });
  await page
    .getByPlaceholder("Enter a URL and press Enter")
    .fill("https://example.com/phase5/login");
  await page.getByPlaceholder("Enter a URL and press Enter").press("Enter");
  await expect(
    page.getByRole("status").filter({ hasText: "Sign in manually in Live" }),
  ).toBeVisible({ timeout: 15_000 });

  // Drive the actual streamed image and keyboard path, not the remote page DOM.
  const image = page.getByAltText("Browser view", { exact: true });
  await expect(image).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("synthetic-login.png") });
  const remoteClick = async (px: number, py: number) => {
    // The full chat sidebar can resize/scroll when keyboard focus changes.
    const box = await image.boundingBox();
    expect(box).not.toBeNull();
    const size = await image.evaluate((element) => {
      const imageElement = element as HTMLImageElement;
      return {
        width: imageElement.naturalWidth,
        height: imageElement.naturalHeight,
      };
    });
    const scale = Math.min(box!.width / size.width, box!.height / size.height);
    const x = box!.x + (box!.width - size.width * scale) / 2;
    const y = box!.y + (box!.height - size.height * scale) / 2;
    await page.mouse.click(x + px * scale * 2, y + py * scale * 2);
  };
  await remoteClick(100, 125);
  await page
    .getByRole("textbox", { name: "Browser keyboard input" })
    .fill("synthetic-user");
  await remoteClick(100, 183);
  await page
    .getByRole("textbox", { name: "Browser keyboard input" })
    .fill("synthetic-password");
  await remoteClick(100, 240);

  const state = async (threadId: string) =>
    (await (await request.get(`/api/phase5-test/page/${threadId}`)).json()) as {
      text: string;
    };
  await expect
    .poll(async () => (await state(MOCK_THREAD_ID)).text)
    .toContain("Cookie + localStorage + IndexedDB restored");
  const remember = page.waitForResponse(
    (response) =>
      response.url().endsWith("/browser/login-state") &&
      response.request().method() === "PUT",
  );
  await page
    .getByRole("button", { name: "Remember login", exact: true })
    .click();
  expect((await remember).status()).toBe(200);
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "Saved login updates automatically" }),
  ).toBeVisible();

  await page.goto(`/workspace/chats/${MOCK_THREAD_ID_2}`);
  await page.getByTestId("browser-trigger").click();
  await expect(
    page.getByRole("button", { name: "Remember login", exact: true }),
  ).toBeEnabled();
  await page
    .getByPlaceholder("Enter a URL and press Enter")
    .fill("https://example.com/phase5/shop?product_id=synthetic");
  await page.getByPlaceholder("Enter a URL and press Enter").press("Enter");
  await expect
    .poll(async () => (await state(MOCK_THREAD_ID_2)).text)
    .toContain("Cookie + localStorage + IndexedDB restored");
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "Saved login updates automatically" }),
  ).toBeVisible();
  // Backend restoration can finish before the actual streamed frame arrives.
  await expect
    .poll(async () =>
      image.evaluate((element) => {
        const canvas = document.createElement("canvas");
        canvas.width = 256;
        canvas.height = 144;
        const context = canvas.getContext("2d")!;
        context.drawImage(element as HTMLImageElement, 0, 0, 256, 144);
        const pixels = context.getImageData(0, 0, 256, 144).data;
        let dark = 0;
        for (let index = 0; index < pixels.length; index += 4) {
          if (
            pixels[index]! < 100 &&
            pixels[index + 1]! < 100 &&
            pixels[index + 2]! < 100
          )
            dark++;
        }
        return dark;
      }),
    )
    .toBeGreaterThan(10);
  await page.screenshot({
    path: testInfo.outputPath("synthetic-restored.png"),
  });
  await page
    .getByRole("button", { name: "Forget all logins", exact: true })
    .click();
  await expect
    .poll(async () => (await state(MOCK_THREAD_ID)).text)
    .toBe("closed");
  await expect
    .poll(async () => (await state(MOCK_THREAD_ID_2)).text)
    .toBe("closed");
  await page.getByTitle("Take live control", { exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Sign in manually in Live" }),
  ).toBeVisible();
});
