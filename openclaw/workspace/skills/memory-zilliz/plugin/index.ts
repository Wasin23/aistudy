/**
 * Zilliz Vector Memory Plugin for OpenClaw
 *
 * Exposes zilliz_recall and zilliz_store as agent tools.
 * Shells out to the Python scripts in the parent tools/ directory.
 */

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { Type } from "@sinclair/typebox";

const execFileAsync = promisify(execFile);

// Load .env from workspace root (4 levels up: plugin/ -> memory-zilliz/ -> skills/ -> workspace/)
const workspaceRoot = resolve(__dirname, "../../../..");
const envPath = join(workspaceRoot, ".env");
const toolsDir = resolve(__dirname, "../tools");

function loadEnv(): Record<string, string> {
  try {
    const contents = readFileSync(envPath, "utf8");
    const vars: Record<string, string> = {};
    for (const line of contents.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const idx = trimmed.indexOf("=");
      if (idx === -1) continue;
      const key = trimmed.slice(0, idx).trim();
      const val = trimmed.slice(idx + 1).trim();
      vars[key] = val;
    }
    return vars;
  } catch {
    return {};
  }
}

async function runPython(script: string, args: string[]): Promise<unknown> {
  const env = { ...process.env, ...loadEnv() };
  const { stdout, stderr } = await execFileAsync("python3", [script, ...args], {
    env,
    timeout: 30000,
  });
  if (stderr) {
    console.warn(`[memory-zilliz] stderr: ${stderr}`);
  }
  return JSON.parse(stdout);
}

const plugin = {
  id: "memory-zilliz",
  name: "Memory (Zilliz)",
  description: "Zilliz/Milvus vector memory — recall and store memories via semantic search",

  register(api: any) {
    // zilliz_recall tool
    api.registerTool(
      {
        name: "zilliz_recall",
        description:
          "Search long-term vector memory for relevant context. Use when the user references past conversations, says 'remember', 'you know', or asks about prior context.",
        parameters: Type.Object({
          query: Type.String({ description: "Natural language search query" }),
          limit: Type.Optional(
            Type.Number({ description: "Max results to return (default 5)", default: 5 })
          ),
        }),
        async execute(_id: string, params: { query: string; limit?: number }) {
          const script = join(toolsDir, "zilliz_recall.py");
          const args = [params.query, String(params.limit ?? 5)];
          const result = await runPython(script, args);
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(result, null, 2),
              },
            ],
          };
        },
      },
      { optional: true }
    );

    // zilliz_store tool
    api.registerTool(
      {
        name: "zilliz_store",
        description:
          "Store a memory in long-term vector storage. Use to save user preferences, decisions, facts, project context, or anything worth remembering across sessions.",
        parameters: Type.Object({
          content: Type.String({ description: "The memory text to store" }),
          category: Type.Optional(
            Type.String({
              description:
                "Category: user_info, preferences, facts, project, lesson, general (default: general)",
              default: "general",
            })
          ),
          importance: Type.Optional(
            Type.Number({
              description: "Importance 1-5 (5=critical, always retrieve; default: 3)",
              default: 3,
            })
          ),
        }),
        async execute(
          _id: string,
          params: { content: string; category?: string; importance?: number }
        ) {
          const script = join(toolsDir, "zilliz_store.py");
          const args = [
            params.content,
            params.category ?? "general",
            String(params.importance ?? 3),
          ];
          const result = await runPython(script, args);
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(result, null, 2),
              },
            ],
          };
        },
      },
      { optional: true }
    );
  },
};

export default plugin;
