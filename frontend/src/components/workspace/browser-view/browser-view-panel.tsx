"use client";

import {
  ArrowLeftIcon,
  ArrowRightIcon,
  GlobeIcon,
  Loader2Icon,
  LockKeyholeIcon,
  LogOutIcon,
  MonitorIcon,
  RadioIcon,
  XIcon,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { ConversationEmptyState } from "@/components/ai-elements/conversation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { resolveArtifactURL } from "@/core/artifacts/utils";
import { isIMEComposing } from "@/lib/ime";
import { cn } from "@/lib/utils";

import {
  forgetBrowserLogin,
  navigateBrowser,
  rememberBrowserLogin,
} from "./api";
import { useMaybeBrowserView } from "./context";
import { decideBrowserKeyInput } from "./keyboard";
import { type BrowserInputEvent, useBrowserStream } from "./use-browser-stream";

export function BrowserViewPanel({
  threadId,
  className,
}: {
  threadId: string;
  className?: string;
}) {
  const browserView = useMaybeBrowserView();
  const frame = browserView?.latestFrame ?? null;
  const imageUrl = frame
    ? resolveArtifactURL(frame.screenshot, threadId)
    : null;

  const [urlInput, setUrlInput] = useState("");
  const [navigating, setNavigating] = useState(false);
  const [live, setLive] = useState(true);
  const [loginAction, setLoginAction] = useState<"remember" | "forget" | null>(
    null,
  );
  const [lastLiveUrl, setLastLiveUrl] = useState<string | null>(null);
  const [liveFallback, setLiveFallback] = useState<{
    frameUrl: string;
    url?: string;
  } | null>(null);

  const streamSeedUrl = lastLiveUrl ?? liveFallback?.url ?? frame?.url;
  const handleNavRejected = useCallback(
    (url: string | undefined, message: string | undefined) => {
      setNavigating(false);
      toast.error(
        message?.replace(/^Error:\s*/i, "") ??
          `Cannot open ${url ?? "that URL"}`,
      );
    },
    [],
  );
  const { status, frameUrl, liveUrl, tabs, loginStatus, sendInput } =
    useBrowserStream(threadId, live, streamSeedUrl, handleNavRejected);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const keyboardRef = useRef<HTMLTextAreaElement | null>(null);
  const composingRef = useRef(false);
  const dragRef = useRef<{
    x: number;
    y: number;
    nx: number;
    ny: number;
    dragging: boolean;
  } | null>(null);
  const suppressClickRef = useRef(false);
  const surfaceRef = useRef<HTMLImageElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const staticScreenshotRef = useRef<string | null>(null);
  // True while the user is actively editing the URL bar, so background live-URL
  // reports do not clobber a half-typed address the user has not submitted yet.
  const urlEditingRef = useRef(false);
  // Handle for the live-navigate spinner timeout so it can be cleared on
  // unmount / re-navigation instead of firing setState after teardown.
  const navSpinnerTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (navSpinnerTimerRef.current !== null) {
        window.clearTimeout(navSpinnerTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    setLastLiveUrl(null);
  }, [threadId]);

  useEffect(() => {
    if (frame?.url && !urlInput && !liveUrl) {
      setUrlInput(frame.url);
    }
  }, [frame?.url, liveUrl, urlInput]);

  // Keep the URL bar in sync with the latest visible browser state while not
  // live. If the user leaves Live mode, the last streamed frame becomes the
  // static baseline instead of falling back to an older artifact screenshot.
  useEffect(() => {
    if (!live) {
      const url = liveFallback?.url ?? frame?.url;
      if (url) {
        setUrlInput(url);
      }
    }
  }, [frame?.url, live, liveFallback?.url]);

  useEffect(() => {
    const screenshot = frame?.screenshot ?? null;
    if (screenshot && screenshot !== staticScreenshotRef.current) {
      staticScreenshotRef.current = screenshot;
      setLiveFallback(null);
    }
  }, [frame?.screenshot]);

  useEffect(() => {
    if (frameUrl) {
      setLiveFallback((prev) => ({
        frameUrl,
        url: liveUrl ?? prev?.url ?? (urlInput || frame?.url),
      }));
    }
  }, [frame?.url, frameUrl, liveUrl, urlInput]);

  // In live mode the server reports the page's real URL (after redirects and
  // history moves). Reconcile the address bar + device-shell label + persisted
  // frame so the top URL never goes stale after navigation.
  useEffect(() => {
    if (live && liveUrl) {
      setLastLiveUrl(liveUrl);
      if (!urlEditingRef.current) {
        setUrlInput(liveUrl === "about:blank" ? "" : liveUrl);
      }
      setNavigating(false);
      setLiveFallback((prev) => (prev ? { ...prev, url: liveUrl } : prev));
    }
  }, [liveUrl, live]);

  const handleNavigate = async () => {
    const target = urlInput.trim();
    if (!target) {
      return;
    }
    const normalized = /^https?:\/\//i.test(target)
      ? target
      : `https://${target}`;

    // In live mode, steer the streamed page directly over the socket. The
    // screencast streams continuously, so there is no single "done" frame to
    // key off — show the reload spinner for a brief window so the user gets
    // clear feedback that the navigation actually took. Also sync the URL
    // everywhere immediately (URL bar, device-shell label, persisted frame).
    if (live) {
      sendInput({ type: "navigate", url: normalized });
      setUrlInput(normalized);
      urlEditingRef.current = false;
      setLiveFallback((prev) => (prev ? { ...prev, url: normalized } : prev));
      setNavigating(true);
      if (navSpinnerTimerRef.current !== null) {
        window.clearTimeout(navSpinnerTimerRef.current);
      }
      navSpinnerTimerRef.current = window.setTimeout(() => {
        navSpinnerTimerRef.current = null;
        setNavigating(false);
      }, 1200);
      return;
    }

    if (navigating) {
      return;
    }
    setNavigating(true);
    try {
      const result = await navigateBrowser(threadId, normalized);
      if (result.screenshot) {
        setLiveFallback(null);
        browserView?.pushFrame({
          screenshot: result.screenshot,
          url: result.url,
          title: result.title,
        });
      } else {
        setUrlInput(result.url);
        toast.warning("Navigated, but no screenshot could be captured.");
      }
      browserView?.openPanel();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error));
    } finally {
      setNavigating(false);
    }
  };

  const handleLoginState = async (action: "remember" | "forget") => {
    if (loginAction) return;
    setLoginAction(action);
    try {
      if (action === "remember") {
        await rememberBrowserLogin(threadId);
        toast.success(
          "Login state saved for your future browser sessions. Websites may ask you to sign in again when it expires.",
        );
      } else {
        await forgetBrowserLogin(threadId);
        setLive(false);
        setLiveFallback(null);
        toast.success(
          "Saved website logins cleared. Open Live again to use a fresh browser.",
        );
      }
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Could not update saved website logins",
      );
    } finally {
      setLoginAction(null);
    }
  };

  const normalizedPoint = useCallback(
    (
      clientX: number,
      clientY: number,
      options?: { fallbackToCenter?: boolean },
    ): { nx: number; ny: number } | null => {
      const el = surfaceRef.current;
      if (!el) {
        return null;
      }
      const rect = el.getBoundingClientRect();
      const natW = el.naturalWidth;
      const natH = el.naturalHeight;
      if (!rect.width || !rect.height || !natW || !natH) {
        return null;
      }
      // The frame is drawn with object-contain: scaled to fit and centered, so
      // there are letterbox bars whenever the panel and remote viewport differ
      // in aspect. Map the pointer against the actual content box.
      const scale = Math.min(rect.width / natW, rect.height / natH);
      const contentW = natW * scale;
      const contentH = natH * scale;
      const offX = (rect.width - contentW) / 2;
      const offY = (rect.height - contentH) / 2;
      const px = clientX - rect.left - offX;
      const py = clientY - rect.top - offY;
      if (px < 0 || py < 0 || px > contentW || py > contentH) {
        if (options?.fallbackToCenter) {
          return { nx: 0.5, ny: 0.5 };
        }
        return null;
      }
      return { nx: px / contentW, ny: py / contentH };
    },
    [],
  );

  const forwardMouse = (
    type: Extract<BrowserInputEvent, { nx: number }>["type"],
    event: React.MouseEvent<HTMLImageElement>,
  ) => {
    if (!live) {
      return;
    }
    const point = normalizedPoint(event.clientX, event.clientY);
    if (point) {
      sendInput({ type, ...point });
    }
  };

  const liveActive = live && status === "open";
  const liveConnecting = live && status === "connecting";
  const displayUrl = live
    ? (frameUrl ?? liveFallback?.frameUrl ?? imageUrl)
    : (liveFallback?.frameUrl ?? imageUrl);

  useEffect(() => {
    const input = keyboardRef.current;
    if (!input) return;
    const start = () => {
      composingRef.current = true;
    };
    const end = (event: CompositionEvent) => {
      composingRef.current = false;
      const text = event.data ?? input.value;
      if (liveActive && text) sendInput({ type: "text", text });
      input.value = "";
    };
    input.addEventListener("compositionstart", start);
    input.addEventListener("compositionend", end);
    return () => {
      input.removeEventListener("compositionstart", start);
      input.removeEventListener("compositionend", end);
    };
  }, [liveActive, sendInput]);

  // React registers onWheel as a passive listener, so preventDefault() there is
  // ignored and the wheel scrolls the host chat page. Bind a native, non-passive
  // listener on the always-mounted stage (the <img> may not exist yet when live
  // first opens) so scrolling stays captured inside the remote page.
  useEffect(() => {
    const el = stageRef.current;
    if (!el || !liveActive) {
      return;
    }
    let wheelFrame: number | null = null;
    let pendingDx = 0;
    let pendingDy = 0;
    let pendingPoint: { nx: number; ny: number } | null = null;

    const browserWheelDelta = (pixels: number) => {
      return Math.abs(pixels) < 0.25 ? 0 : pixels * 2;
    };

    const flushWheel = () => {
      wheelFrame = null;
      const dx = browserWheelDelta(pendingDx);
      const dy = browserWheelDelta(pendingDy);
      const point = pendingPoint;
      pendingDx = 0;
      pendingDy = 0;
      pendingPoint = null;
      if (dx || dy) {
        sendInput({ type: "wheel", dx, dy, ...(point ?? {}) });
      }
    };

    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      event.stopPropagation();
      // Normalize deltaMode (line/page → pixels), then batch one animation
      // frame of deltas. A small 2x gain keeps touchpad gestures responsive
      // without returning to the jumpy large-step behavior.
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 800 : 1;
      pendingDx += event.deltaX * unit;
      pendingDy += event.deltaY * unit;
      const point = normalizedPoint(event.clientX, event.clientY, {
        fallbackToCenter: true,
      });
      if (point) {
        pendingPoint = point;
      }
      wheelFrame ??= window.requestAnimationFrame(flushWheel);
    };
    el.addEventListener("wheel", onWheel, {
      capture: true,
      passive: false,
    });
    return () => {
      el.removeEventListener("wheel", onWheel, { capture: true });
      if (wheelFrame !== null) {
        window.cancelAnimationFrame(wheelFrame);
      }
    };
  }, [liveActive, normalizedPoint, sendInput]);

  return (
    <div
      ref={panelRef}
      className={cn(
        "bg-background relative flex flex-col",
        "size-full",
        className,
      )}
      tabIndex={live ? 0 : undefined}
      onKeyDown={(event) => {
        if (event.target === keyboardRef.current) return;
        const target = event.target;
        const editableTarget =
          target instanceof HTMLInputElement ||
          target instanceof HTMLTextAreaElement ||
          (target instanceof HTMLElement && target.isContentEditable);
        const input = decideBrowserKeyInput({
          live,
          editableTarget,
          composing: isIMEComposing(event),
          key: event.key,
          metaKey: event.metaKey,
          ctrlKey: event.ctrlKey,
        });
        if (!input) {
          return;
        }
        sendInput(input);
        event.preventDefault();
        event.stopPropagation();
      }}
    >
      <header className="flex shrink-0 items-center gap-2 border-b px-3 py-2">
        <MonitorIcon className="size-4 shrink-0" />
        <span className="shrink-0 text-sm font-medium">Browser</span>
        <div className="flex shrink-0 items-center">
          <Button
            size="icon-sm"
            variant="ghost"
            className="shrink-0"
            disabled={!live}
            onClick={() => sendInput({ type: "back" })}
            title="Back"
          >
            <ArrowLeftIcon />
          </Button>
          <Button
            size="icon-sm"
            variant="ghost"
            className="shrink-0"
            disabled={!live}
            onClick={() => sendInput({ type: "forward" })}
            title="Forward"
          >
            <ArrowRightIcon />
          </Button>
        </div>
        <form
          className="relative flex min-w-0 flex-1 items-center"
          onSubmit={(event) => {
            event.preventDefault();
            void handleNavigate();
          }}
        >
          <GlobeIcon className="text-muted-foreground pointer-events-none absolute left-2 size-3.5" />
          <Input
            value={urlInput}
            onChange={(event) => {
              urlEditingRef.current = true;
              setUrlInput(event.target.value);
            }}
            onFocus={(event) => {
              urlEditingRef.current = true;
              event.currentTarget.select();
            }}
            onBlur={() => {
              urlEditingRef.current = false;
            }}
            onKeyDown={(event) => {
              // Keep browser select-all/copy/cut/paste working inside the URL
              // bar; stop the panel + global shortcut handlers from swallowing.
              event.stopPropagation();
            }}
            placeholder="Enter a URL and press Enter"
            spellCheck={false}
            autoComplete="off"
            className="h-8 pl-7 text-xs"
          />
          {navigating && (
            <Loader2Icon className="text-muted-foreground absolute right-2 size-3.5 animate-spin" />
          )}
        </form>
        <Button
          size="sm"
          variant={live ? "default" : "ghost"}
          className="shrink-0 gap-1"
          onClick={() => setLive((prev) => !prev)}
          title={live ? "Stop live control" : "Take live control"}
        >
          <RadioIcon className="size-3.5" />
          {live ? (status === "open" ? "Live" : "…") : "Live"}
        </Button>
        <Button
          size="icon-sm"
          variant="ghost"
          className="shrink-0"
          onClick={() => {
            setLive(false);
            browserView?.close();
          }}
        >
          <XIcon />
        </Button>
      </header>
      <div className="flex flex-wrap items-center gap-2 border-b px-3 py-2">
        {tabs.length > 1 && (
          <select
            aria-label="Browser tab"
            className="bg-background max-w-48 min-w-0 rounded border px-2 py-1 text-xs"
            value={tabs.find((tab) => tab.active)?.index ?? 0}
            onChange={(event) =>
              sendInput({
                type: "activate_tab",
                index: Number(event.target.value),
              })
            }
          >
            {tabs.map((tab) => (
              <option key={tab.index} value={tab.index}>
                {tab.title || `Tab ${tab.index + 1}`}
              </option>
            ))}
          </select>
        )}
        <Button
          size="sm"
          variant="outline"
          disabled={loginAction !== null || !live || status !== "open"}
          onClick={() => void handleLoginState("remember")}
        >
          {loginAction === "remember" ? (
            <Loader2Icon className="size-3.5 animate-spin" />
          ) : (
            <LockKeyholeIcon className="size-3.5" />
          )}
          Remember login
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={loginAction !== null}
          onClick={() => void handleLoginState("forget")}
          title="Clear all saved website logins and close your active browser sessions"
        >
          <LogOutIcon className="size-3.5" />
          Forget all logins
        </Button>
        <span className="text-muted-foreground text-xs" role="status">
          {loginStatus?.notice === "login_required"
            ? "Sign in manually in Live, then Remember login. Never send passwords or codes in chat."
            : loginStatus?.notice === "state_changed"
              ? "Saved login changed in another browser. Close this browser and reopen it before saving."
              : loginStatus?.notice === "state_cleared"
                ? "Browser session closed. Reopen Live to load saved logins or sign in again."
                : loginStatus?.notice === "save_failed" ||
                    loginStatus?.notice === "storage_unavailable"
                  ? "Login could not be saved. Retry Remember login, or clear saved logins and sign in again."
                  : loginStatus?.remembered
                    ? "Saved login updates automatically while this browser is open."
                    : "Sign in here, then Remember login to reuse it in your other chats."}
        </span>
      </div>
      <textarea
        ref={keyboardRef}
        aria-label="Browser keyboard input"
        className="sr-only"
        autoComplete="off"
        spellCheck={false}
        onInput={(event) => {
          if (composingRef.current || event.nativeEvent.isComposing) return;
          const text = event.currentTarget.value;
          if (liveActive && text) sendInput({ type: "text", text });
          event.currentTarget.value = "";
        }}
        onPaste={(event) => {
          event.preventDefault();
          const text = event.clipboardData.getData("text/plain");
          if (liveActive && text) sendInput({ type: "text", text });
          event.currentTarget.value = "";
        }}
        onKeyDown={(event) => {
          event.stopPropagation();
          if (isIMEComposing(event)) return;
          if (event.key.length === 1 && !event.metaKey && !event.ctrlKey)
            return;
          if (
            (event.metaKey || event.ctrlKey) &&
            event.key.toLowerCase() === "v"
          )
            return;
          const input = decideBrowserKeyInput({
            live: liveActive,
            editableTarget: false,
            composing: false,
            key: event.key,
            metaKey: event.metaKey,
            ctrlKey: event.ctrlKey,
          });
          if (input) {
            sendInput(input);
            event.preventDefault();
          }
        }}
      />
      <main className="relative flex min-h-0 grow flex-col overflow-hidden bg-neutral-950">
        <div
          ref={stageRef}
          className="relative min-h-0 grow bg-neutral-900"
          onMouseDown={() => {
            keyboardRef.current?.focus({ preventScroll: true });
          }}
        >
          {displayUrl ? (
            <img
              ref={surfaceRef}
              className="absolute inset-0 h-full w-full cursor-default object-contain object-center"
              src={displayUrl}
              alt={frame?.title ?? "Browser view"}
              draggable={false}
              onPointerDown={(event) => {
                if (!liveActive || event.button !== 0) return;
                const point = normalizedPoint(event.clientX, event.clientY);
                if (point) {
                  dragRef.current = {
                    ...point,
                    x: event.clientX,
                    y: event.clientY,
                    dragging: false,
                  };
                  event.currentTarget.setPointerCapture(event.pointerId);
                }
              }}
              onPointerMove={(event) => {
                const drag = dragRef.current;
                if (!drag) return;
                const point = normalizedPoint(event.clientX, event.clientY, {
                  fallbackToCenter: true,
                });
                if (!point) return;
                if (
                  !drag.dragging &&
                  Math.hypot(event.clientX - drag.x, event.clientY - drag.y) >=
                    5
                ) {
                  drag.dragging = true;
                  sendInput({ type: "down", nx: drag.nx, ny: drag.ny });
                }
                if (drag.dragging) sendInput({ type: "move", ...point });
              }}
              onPointerUp={(event) => {
                const drag = dragRef.current;
                if (drag?.dragging) {
                  const point = normalizedPoint(event.clientX, event.clientY, {
                    fallbackToCenter: true,
                  });
                  sendInput({
                    type: "up",
                    nx: point?.nx ?? drag.nx,
                    ny: point?.ny ?? drag.ny,
                  });
                  suppressClickRef.current = true;
                }
                dragRef.current = null;
              }}
              onPointerCancel={() => {
                const drag = dragRef.current;
                if (drag?.dragging)
                  sendInput({ type: "up", nx: drag.nx, ny: drag.ny });
                dragRef.current = null;
              }}
              onClick={(event) => {
                if (suppressClickRef.current) {
                  suppressClickRef.current = false;
                  return;
                }
                forwardMouse("click", event);
              }}
            />
          ) : (
            <ConversationEmptyState
              className="absolute inset-0 m-auto h-fit"
              icon={<MonitorIcon />}
              title={
                live ? "Connecting to live browser…" : "No browser activity yet"
              }
              description={
                live
                  ? "Waiting for the first live frame."
                  : "Enter a URL above or let the agent browse — the live view will appear here."
              }
            />
          )}
          {(navigating || liveConnecting) && displayUrl && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/40 backdrop-blur-[1px]">
              <Loader2Icon className="text-muted-foreground size-8 animate-spin" />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
