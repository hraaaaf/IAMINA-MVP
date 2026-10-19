import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { getVercelOidcToken } from '@vercel/oidc';

const WEB_PROJECT = 'prj_AYaUi32KTDHak8I7dmdQpDrqd8SI';
const EXACT_API_ORIGIN =
  'https://iamina-certified-1mrvxnuk9-achraf-benmoussa-s-projects.vercel.app';
const MAX_REQUEST_BYTES = 4 * 1024 * 1024;

class PayloadTooLargeError extends Error {}

async function readBoundedBody(request) {
  const parts = [];
  let received = 0;
  // Read and cap actual bytes, not only the caller-controlled Content-Length.
  // Never begin upstream egress until this completes successfully.
  for await (const value of request) {
    const chunk = Buffer.isBuffer(value) ? value : Buffer.from(value);
    received += chunk.length;
    if (received > MAX_REQUEST_BYTES) throw new PayloadTooLargeError();
    parts.push(chunk);
  }
  return Buffer.concat(parts, received);
}
const ALLOWED_METHODS = new Set(['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']);
const RESPONSE_HEADERS = ['content-type', 'content-disposition', 'etag', 'last-modified'];
const WEB_HOST = /^iamina-review-[a-z0-9-]+-achraf-benmoussa-s-projects\.vercel\.app$/;

function safePath(value) {
  if (typeof value !== 'string' || !value || value.length > 1024 ||
      value.startsWith('/') || value.includes('\\') || value.includes('%') ||
      value.includes('//')) return false;
  // Django has canonical endpoints ending in '/'. Only a single terminal
  // slash is acceptable: empty middle segments and traversal remain blocked.
  const segments = (value.endsWith('/') ? value.slice(0, -1) : value).split('/');
  return segments.every((part) =>
    part !== '.' && part !== '..' &&
    /^[A-Za-z0-9][A-Za-z0-9_.~-]*$/.test(part));
}

function requestPath(request) {
  const original = new URL(request.url, 'https://internal.invalid');
  // Vercel may expose either original path or rewritten function path.
  const rawPath = original.pathname.startsWith('/api/v1/')
    ? original.pathname.slice('/api/v1/'.length)
    : request.query?.path;
  if (!safePath(rawPath)) return null;
  original.searchParams.delete('path'); // Internal rewrite capture, not patient data.
  return { path: rawPath, search: original.search };
}

function previewOnlyAndSameOrigin(request) {
  if (process.env.VERCEL_ENV !== 'preview' ||
      process.env.VERCEL_PROJECT_ID !== WEB_PROJECT) return 404;
  const host = request.headers.host;
  if (typeof host !== 'string' || !WEB_HOST.test(host)) return 403;
  const origin = request.headers.origin;
  if (origin !== undefined && origin !== 'https://' + host) return 403;
  // No cookie transport between Vercel SSO and Django. Django uses IAMINA bearer.
  if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method) && !origin) return 403;
  return 0;
}

export const config = {
  api: { bodyParser: false },
  maxDuration: 30,
};

export async function proxy(request, response, getToken = getVercelOidcToken) {
  response.setHeader('Cache-Control', 'private, no-store, max-age=0');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  const gate = previewOnlyAndSameOrigin(request);
  if (gate) return response.status(gate).end();
  if (!ALLOWED_METHODS.has(request.method)) return response.status(405).end();
  const route = requestPath(request);
  if (!route) return response.status(400).end();
  const length = Number(request.headers['content-length'] ?? '0');
  if (!Number.isSafeInteger(length) || length < 0 ||
      length > MAX_REQUEST_BYTES) return response.status(413).end();

  // Fail closed on missing/incorrect configuration; no fallback to production.
  if (process.env.IAMINA_REVIEW_PREVIEW_API_BASE_URL !== EXACT_API_ORIGIN) {
    return response.status(503).end();
  }
  // Vercel Trusted Sources authenticates this Preview-to-Preview workload.
  // No project-wide automation bypass is provisioned or shared with Flutter.
  let oidcToken;
  try { oidcToken = await getToken(); } catch { return response.status(503).end(); }
  if (typeof oidcToken !== 'string' || oidcToken.length < 3)
    return response.status(503).end();

  let payload;
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    try {
      payload = await readBoundedBody(request);
    } catch (error) {
      return response.status(error instanceof PayloadTooLargeError ? 413 : 400).end();
    }
  }

  const outgoingHeaders = new Headers();
  outgoingHeaders.set('x-vercel-trusted-oidc-idp-token', oidcToken);
  for (const name of ['authorization', 'accept', 'content-type', 'if-match', 'if-none-match']) {
    const value = request.headers[name];
    if (typeof value === 'string') outgoingHeaders.set(name, value);
  }
  // Never forward browser cookies, Origin, Host, IP assertions, arbitrary
  // x-* headers, or client-supplied deployment-protection secrets.
  try {
    const upstream = await fetch(EXACT_API_ORIGIN + '/api/v1/' + route.path + route.search, {
      method: request.method,
      headers: outgoingHeaders,
      body: payload,
      duplex: 'half',
      redirect: 'manual',
      cache: 'no-store',
      signal: AbortSignal.timeout(25000),
    });
    // No redirect or HTML login challenge from Deployment Protection may
    // masquerade as a successful Django API response.
    const type = (upstream.headers.get('content-type') ?? '').toLowerCase();
    if ((upstream.status >= 300 && upstream.status < 400) ||
        type.includes('text/html') || type.includes('application/xhtml+xml')) {
      await upstream.body?.cancel();
      return response.status(502).end();
    }
    response.status(upstream.status);
    for (const name of RESPONSE_HEADERS) {
      const value = upstream.headers.get(name);
      if (value) response.setHeader(name, value);
    }
    // Never propagate Set-Cookie, upstream CORS or caching headers.
    if (request.method === 'HEAD' || !upstream.body) {
      await upstream.body?.cancel();
      return response.end();
    }
    await pipeline(Readable.fromWeb(upstream.body), response);
  } catch {
    // Do not expose secrets, patient payloads or remote target to the client.
    if (!response.headersSent) return response.status(502).end();
    response.end();
  }
}

export default async function handler(request, response) {
  return proxy(request, response);
}

export { safePath, requestPath, previewOnlyAndSameOrigin };
