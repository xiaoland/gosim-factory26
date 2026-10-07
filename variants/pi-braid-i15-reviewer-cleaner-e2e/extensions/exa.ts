import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type, type Static } from "typebox";

const contentOptions = {
  text: Type.Optional(Type.Boolean({ description: "Include page text." })),
  highlights: Type.Optional(Type.Boolean({ description: "Include relevant text excerpts." })),
  maxAgeHours: Type.Optional(Type.Number({ minimum: 0, description: "Maximum cached content age in hours; 0 requests fresh retrieval." })),
  livecrawlTimeout: Type.Optional(Type.Integer({ minimum: 1000, maximum: 120000, description: "Content retrieval timeout in milliseconds." })),
};
const outputLimit = Type.Optional(Type.Integer({ minimum: 500, maximum: 20000, description: "Maximum returned characters per page text/excerpt (default 6000); output also has a shared 30000-character text budget. Source URLs and truncation counts remain available." }));
const Search = Type.Object({
  query: Type.String({ minLength: 1, description: "Web search query, sent to Exa; exclude credentials and private information." }),
  type: Type.Optional(Type.Union([Type.Literal("auto"), Type.Literal("neural"), Type.Literal("fast")], { description: "Search method (default auto)." })),
  numResults: Type.Optional(Type.Integer({ minimum: 1, maximum: 100, description: "Number of results (default 10)." })),
  includeDomains: Type.Optional(Type.Array(Type.String({ minLength: 1 }), { description: "Restrict results to these domains." })),
  excludeDomains: Type.Optional(Type.Array(Type.String({ minLength: 1 }), { description: "Exclude these domains." })),
  startPublishedDate: Type.Optional(Type.String({ format: "date-time", description: "Earliest publication date, ISO 8601." })),
  endPublishedDate: Type.Optional(Type.String({ format: "date-time", description: "Latest publication date, ISO 8601." })),
  contents: Type.Optional(Type.Object(contentOptions, { description: "Content retrieval options; default includes highlights." })),
  maxCharacters: outputLimit,
});
const Contents = Type.Object({
  urls: Type.Array(Type.String({ minLength: 1, maxLength: 2048 }), { minItems: 1, maxItems: 100, description: "HTTP(S) source URLs from search results or already known pages; sent to Exa." }),
  ...contentOptions,
  maxCharacters: outputLimit,
});

type Page = {
  id?: string; title?: string; url?: string; publishedDate?: string; author?: string;
  text?: string; highlights?: string[];
};
type ExaResponse = {
  requestId?: string; results?: Page[]; statuses?: unknown[];
  costDollars?: unknown; resolvedSearchType?: string;
};

function redact(text: string): string {
  const key = process.env.EXA_API_KEY;
  return key ? text.split(key).join("[REDACTED]") : text;
}

async function request(endpoint: string, body: object, maxCharacters: number, signal?: AbortSignal) {
  const key = process.env.EXA_API_KEY;
  if (!key) throw new Error("EXA_API_KEY is required for Exa tools.");
  const response = await fetch(`https://api.exa.ai/${endpoint}`, {
    method: "POST",
    headers: { "x-api-key": key, "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(130000)]) : AbortSignal.timeout(130000),
  });
  const raw = redact(await response.text());
  const headerId = response.headers.get("x-request-id") || response.headers.get("request-id");
  let data: ExaResponse;
  try {
    data = JSON.parse(raw);
  } catch {
    throw new Error(`Exa HTTP ${response.status} ${response.statusText}${headerId ? `; request ID: ${headerId}` : ""}; non-JSON response\n${raw.slice(0, 8000)}${raw.length > 8000 ? `\n[Response truncated: ${raw.length} characters]` : ""}`);
  }
  if (!data || typeof data !== "object") throw new Error(`Exa HTTP ${response.status}; unexpected response\n${raw.slice(0, 8000)}`);
  const requestId = data.requestId || headerId;
  if (!response.ok) {
    throw new Error(`Exa HTTP ${response.status} ${response.statusText}${requestId ? `; request ID: ${requestId}` : ""}\n${raw.slice(0, 8000)}${raw.length > 8000 ? `\n[Response truncated: ${raw.length} characters]` : ""}`);
  }
  if (!Array.isArray(data.results)) throw new Error(`Exa HTTP ${response.status}; request ID: ${requestId || "unavailable"}; missing results\n${raw.slice(0, 8000)}`);
  let remaining = 30000;
  function bounded(text: string) {
    const shown = text.slice(0, Math.min(maxCharacters, remaining));
    remaining -= shown.length;
    return { value: shown, originalCharacters: text.length, truncated: shown.length < text.length };
  }
  const results = data.results.map((page) => {
    const { text, highlights, ...source } = page;
    const excerpt = text === undefined ? undefined : bounded(text);
    return {
      ...source,
      ...(excerpt && { text: excerpt.value, textCharacters: excerpt.originalCharacters, textTruncated: excerpt.truncated }),
      ...(highlights && { highlights: highlights.map((highlight) => bounded(highlight)) }),
    };
  });
  const output = { requestId, results, statuses: data.statuses, costDollars: data.costDollars, resolvedSearchType: data.resolvedSearchType };
  return { content: [{ type: "text" as const, text: JSON.stringify(output, null, 2) }], details: { httpStatus: response.status, requestId } };
}

export default function exa(pi: ExtensionAPI) {
  pi.registerTool({
    name: "exa_search", label: "Exa Search",
    description: "Search the web through Exa, returning source URLs and optional page text or relevant excerpts. Filters apply to search results.",
    parameters: Search,
    async execute(_id, params: Static<typeof Search>, signal) {
      const { maxCharacters = 6000, contents = { highlights: true }, ...query } = params;
      return request("search", { ...query, contents }, maxCharacters, signal);
    },
  });
  pi.registerTool({
    name: "exa_contents", label: "Exa Contents",
    description: "Retrieve page contents from Exa for known source URLs, retaining individual retrieval statuses. Page text is enabled by default.",
    parameters: Contents,
    async execute(_id, params: Static<typeof Contents>, signal) {
      const { maxCharacters = 6000, text = true, ...options } = params;
      for (const url of options.urls) {
        if (!["http:", "https:"].includes(new URL(url).protocol)) throw new Error("Exa contents requires HTTP(S) URLs.");
      }
      return request("contents", { ...options, text }, maxCharacters, signal);
    },
  });
}
