import { realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { pluginReact } from "@rsbuild/plugin-react";

// Reuse Rstest's installed bundler; no dependency installation or source copies.
const frontend = fileURLToPath(new URL("../../", import.meta.url));
const require = createRequire(
  realpathSync(resolve(frontend, "node_modules/@rstest/core/package.json")),
);
const { createRsbuild } = await import(
  pathToFileURL(require.resolve("@rsbuild/core"))
);
const bundler = await createRsbuild({
  cwd: frontend,
  rsbuildConfig: {
    plugins: [pluginReact()],
    source: {
      entry: {
        index: fileURLToPath(
          new URL("./browser-login-entry.tsx", import.meta.url),
        ),
      },
      define: {
        "process.env.NEXT_PUBLIC_BACKEND_BASE_URL": '""',
        "process.env.NEXT_PUBLIC_LANGGRAPH_BASE_URL": '""',
        "process.env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY": '"false"',
        "process.env.GITHUB_OAUTH_TOKEN": "undefined",
        "process.env.SKIP_ENV_VALIDATION": '"1"',
      },
    },
    resolve: { alias: { "@": resolve(frontend, "src") } },
    tools: { cssLoader: { url: false } },
    output: {
      cleanDistPath: false,
      distPath: {
        root: resolve(
          frontend,
          "../.deer-flow/local-dev/browser-login-verification/panel-dist",
        ),
      },
    },
  },
});
await bundler.build();
