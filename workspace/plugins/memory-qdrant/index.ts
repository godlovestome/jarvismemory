import { readFileSync } from "node:fs";

type PluginConfig = {
  qdrantUrl?: string;
  collectionName?: string;
  ollamaUrl?: string;
  embeddingModel?: string;
  userId?: string;
  autoRecall?: boolean;
  autoCapture?: boolean;
  maxRecallResults?: number;
  minRecallScore?: number;
  apiKeyEnvVar?: string;
};

type RecallResult = {
  score: number;
  payload: Record<string, unknown>;
};

const DEFAULTS = {
  qdrantUrl: "http://127.0.0.1:6333",
  collectionName: "true_recall",
  ollamaUrl: "http://127.0.0.1:11434",
  embeddingModel: "mxbai-embed-large",
  userId: "",
  autoRecall: true,
  autoCapture: false,
  maxRecallResults: 3,
  minRecallScore: 0.5,
  apiKeyEnvVar: "QDRANT_API_KEY",
} as const;

const XML_ESCAPE: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

function getConfig(rawConfig: PluginConfig | undefined): Required<PluginConfig> {
  return {
    qdrantUrl: rawConfig?.qdrantUrl || DEFAULTS.qdrantUrl,
    collectionName: rawConfig?.collectionName || DEFAULTS.collectionName,
    ollamaUrl: rawConfig?.ollamaUrl || DEFAULTS.ollamaUrl,
    embeddingModel: rawConfig?.embeddingModel || DEFAULTS.embeddingModel,
    userId: rawConfig?.userId || process.env.USER_ID || DEFAULTS.userId,
    autoRecall: rawConfig?.autoRecall ?? DEFAULTS.autoRecall,
    autoCapture: rawConfig?.autoCapture ?? DEFAULTS.autoCapture,
    maxRecallResults: rawConfig?.maxRecallResults ?? DEFAULTS.maxRecallResults,
    minRecallScore: rawConfig?.minRecallScore ?? DEFAULTS.minRecallScore,
    apiKeyEnvVar: rawConfig?.apiKeyEnvVar || DEFAULTS.apiKeyEnvVar,
  };
}

function xmlEscape(text: string): string {
  return text.replace(/[&<>"']/g, (value) => XML_ESCAPE[value] || value);
}

function isLocalUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.hostname === "127.0.0.1" || parsed.hostname === "localhost";
  } catch {
    return false;
  }
}

function contentToText(content: unknown): string {
  if (!content) {
    return "";
  }
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content.map((item) => contentToText(item)).filter(Boolean).join("\n");
  }
  if (typeof content === "object") {
    const record = content as Record<string, unknown>;
    if (typeof record.text === "string") {
      return record.text;
    }
    if (typeof record.content === "string") {
      return record.content;
    }
    if (record.content) {
      return contentToText(record.content);
    }
  }
  return "";
}

function extractLatestUserQuery(event: any): string {
  const messages = Array.isArray(event?.messages)
    ? event.messages
    : Array.isArray(event?.input?.messages)
      ? event.input.messages
      : [];

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message?.role !== "user") {
      continue;
    }
    const text = contentToText(message?.content).trim();
    if (text) {
      return text;
    }
  }

  const fallbacks = [
    contentToText(event?.prompt),
    contentToText(event?.input?.prompt),
    contentToText(event?.input),
  ];
  return fallbacks.find((value) => value.trim())?.trim() || "";
}

function qdrantHeaders(config: Required<PluginConfig>): HeadersInit {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const apiKey = resolveQdrantApiKey(config);
  if (apiKey) {
    headers["api-key"] = apiKey;
  }
  return headers;
}

function resolveQdrantApiKey(config: Required<PluginConfig>): string {
  const envValue = process.env[config.apiKeyEnvVar];
  if (envValue) {
    return envValue;
  }

  try {
    const content = readFileSync("/run/openclaw-memory/secrets.env", "utf-8");
    const match = content.match(/^QDRANT_API_KEY=(.+)$/m);
    if (!match) {
      return "";
    }
    return match[1].trim().replace(/^['"]|['"]$/g, "");
  } catch {
    return "";
  }
}

async function embedQuery(query: string, config: Required<PluginConfig>): Promise<number[]> {
  const response = await fetch(`${config.ollamaUrl.replace(/\/$/, "")}/api/embeddings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: config.embeddingModel, prompt: query }),
  });
  if (!response.ok) {
    throw new Error(`Ollama embedding failed: HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (!Array.isArray(payload?.embedding)) {
    throw new Error("Ollama embedding returned no vector");
  }
  return payload.embedding as number[];
}

async function queryQdrant(vector: number[], config: Required<PluginConfig>): Promise<RecallResult[]> {
  const baseUrl = config.qdrantUrl.replace(/\/$/, "");
  const requestBody: Record<string, unknown> = {
    query: vector,
    limit: config.maxRecallResults,
    with_payload: true,
  };

  if (config.userId) {
    requestBody.filter = {
      must: [{ key: "user_id", match: { value: config.userId } }],
    };
  }

  const response = await fetch(
    `${baseUrl}/collections/${config.collectionName}/points/query`,
    {
      method: "POST",
      headers: qdrantHeaders(config),
      body: JSON.stringify(requestBody),
    },
  );

  if (!response.ok) {
    throw new Error(`Qdrant query failed: HTTP ${response.status}`);
  }

  const payload = await response.json();
  const points = Array.isArray(payload?.result?.points)
    ? payload.result.points
    : Array.isArray(payload?.result)
      ? payload.result
      : [];

  return points
    .map((point: any) => ({
      score: typeof point?.score === "number" ? point.score : 0,
      payload: point?.payload && typeof point.payload === "object" ? point.payload : {},
    }))
    .filter((point: RecallResult) => point.score >= config.minRecallScore);
}

function formatRelevantMemoriesContext(results: RecallResult[]): string {
  const blocks = results.map((result, index) => {
    const gem = String(result.payload.gem || "").trim();
    const context = String(result.payload.context || "").trim();
    const snippet = String(result.payload.snippet || "").trim();
    const source = String(result.payload.source || "true_recall").trim();
    const lines = [
      `[Memory ${index + 1} | score ${result.score.toFixed(3)}]`,
      gem && `Gem: ${xmlEscape(gem)}`,
      context && `Context: ${xmlEscape(context)}`,
      snippet && `Snippet: ${xmlEscape(snippet)}`,
      `Source: ${xmlEscape(source)}`,
    ].filter(Boolean);
    return lines.join("\n");
  });

  return `<relevant-memories>\n${blocks.join("\n\n")}\n</relevant-memories>`;
}

export default function memoryQdrantPlugin(api: any): void {
  const config = getConfig(api?.config);
  if (!config.autoRecall) {
    return;
  }

  if (!isLocalUrl(config.qdrantUrl) || !isLocalUrl(config.ollamaUrl)) {
    console.warn("[memory-qdrant] Non-local URLs are not allowed under CodeShield.");
    return;
  }

  api.on("before_agent_start", async (event: any) => {
    const query = extractLatestUserQuery(event);
    if (!query) {
      return;
    }

    try {
      const vector = await embedQuery(query, config);
      const results = await queryQdrant(vector, config);
      if (!results.length) {
        return;
      }
      return { prependContext: formatRelevantMemoriesContext(results) };
    } catch (error) {
      console.warn(`[memory-qdrant] auto-recall failed: ${String(error)}`);
      return;
    }
  });
}
