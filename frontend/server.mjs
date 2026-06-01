import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer, request as httpRequest } from "node:http";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = join(fileURLToPath(new URL(".", import.meta.url)), "dist");
const port = Number(process.env.PORT ?? 5173);
const backendOrigin = new URL(process.env.BACKEND_API_ORIGIN ?? "http://backend:8000");

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
};

const server = createServer(async (req, res) => {
  if (!req.url) {
    res.writeHead(400);
    res.end("Bad Request");
    return;
  }

  if (req.url.startsWith("/api/")) {
    proxyApiRequest(req, res);
    return;
  }

  await serveStatic(req.url, res);
});

server.listen(port, "0.0.0.0", () => {
  console.log(`BidPilot frontend static server listening on ${port}`);
});

async function serveStatic(url, res) {
  const pathname = decodeURIComponent(new URL(url, "http://localhost").pathname);
  const relativePath = normalize(pathname).replace(/^(\.\.[/\\])+/, "").replace(/^[/\\]+/, "");
  const requestedPath = join(rootDir, relativePath || "index.html");

  const filePath = await resolveFilePath(requestedPath);
  const contentType = contentTypes[extname(filePath)] ?? "application/octet-stream";

  res.writeHead(200, { "Content-Type": contentType });
  createReadStream(filePath).pipe(res);
}

async function resolveFilePath(filePath) {
  try {
    const fileStat = await stat(filePath);
    if (fileStat.isFile()) {
      return filePath;
    }
  } catch {
    // Fall through to SPA entry.
  }
  return join(rootDir, "index.html");
}

function proxyApiRequest(req, res) {
  const target = new URL(req.url, backendOrigin);
  const proxy = httpRequest(
    target,
    {
      method: req.method,
      headers: {
        ...req.headers,
        host: backendOrigin.host,
      },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 502, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );

  proxy.on("error", () => {
    res.writeHead(502, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Backend proxy failed.");
  });

  req.pipe(proxy);
}
