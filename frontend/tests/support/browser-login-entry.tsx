import { useState } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "sonner";

import { BrowserViewPanel } from "@/components/workspace/browser-view/browser-view-panel";
import { BrowserViewProvider } from "@/components/workspace/browser-view/context";
import "@/styles/globals.css";

// Mount the production panel without a second Next.js server or a real account.
function SyntheticBrowserPanel() {
  const [open, setOpen] = useState(false);
  const threadId = location.pathname.split("/").pop()!;
  return (
    <BrowserViewProvider>
      <button data-testid="browser-trigger" onClick={() => setOpen(true)}>
        Browser
      </button>
      {open && (
        <div style={{ height: "90vh", width: "100%" }}>
          <BrowserViewPanel threadId={threadId} />
        </div>
      )}
      <Toaster />
    </BrowserViewProvider>
  );
}

createRoot(document.getElementById("root")!).render(<SyntheticBrowserPanel />);
