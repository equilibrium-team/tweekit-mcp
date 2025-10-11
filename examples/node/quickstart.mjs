/**
 * Minimal Node.js quickstart for connecting to the TweekIT MCP server.
 *
 * Usage:
 *   node examples/node/quickstart.mjs --file path/to/input.pdf --outfmt txt
 *
 * Requires: npm install @modelcontextprotocol/sdk
 */

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { argv } from "node:process";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";

const DEFAULT_SERVER = process.env.TWEEKIT_MCP_SERVER ?? "https://mcp.tweekit.com/mcp";
const API_KEY = process.env.TWEAKIT_API_KEY;
const API_SECRET = process.env.TWEAKIT_API_SECRET;

function parseArgs() {
  const args = new URLSearchParams();
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error("Arguments must be provided as --flag value pairs.");
    }
    args.set(key.slice(2), value);
  }
  return {
    file: args.get("file"),
    outfmt: args.get("outfmt"),
    width: Number(args.get("width") ?? 0),
    height: Number(args.get("height") ?? 0),
    page: Number(args.get("page") ?? 1),
    bgcolor: args.get("bgcolor") ?? "",
  };
}

function requireCredential(value, name) {
  if (!value) {
    throw new Error(`Missing ${name}. Set the environment variable or update payload headers.`);
  }
  return value;
}

async function toBase64(filePath) {
  const data = await fs.readFile(filePath);
  return data.toString("base64");
}

async function main() {
  const { file, outfmt, width, height, page, bgcolor } = parseArgs();
  if (!file || !outfmt) {
    throw new Error("Usage: node quickstart.mjs --file <path> --outfmt <format>");
  }

  const client = await Client.connect({
    url: DEFAULT_SERVER,
    headers: {
      ApiKey: requireCredential(API_KEY, "TWEAKIT_API_KEY"),
      ApiSecret: requireCredential(API_SECRET, "TWEAKIT_API_SECRET"),
    },
  });

  try {
    const tools = await client.listTools();
    console.log("Tools available:", tools.map((tool) => tool.name));

    const payload = {
      apiKey: API_KEY,
      apiSecret: API_SECRET,
      inext: path.extname(file).replace(".", "") || "bin",
      outfmt,
      blob: await toBase64(file),
      width,
      height,
      page,
      bgcolor,
    };

    const result = await client.callTool("convert", payload);
    if (result.isError) {
      console.error("Conversion failed:", result.error);
    } else {
      console.log("Conversion result:", result.data ?? result.structuredContent ?? result.content);
    }
  } finally {
    await client.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
