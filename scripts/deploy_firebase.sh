#!/usr/bin/env bash
# Deploy TweekIT MCP to Firebase Functions + Hosting
#
# Usage:
#   bash scripts/deploy_firebase.sh -p <PROJECT_ID> [-r <REGION>] [--skip-vendor] [--use-uv|--use-pip] [--no-hosting|--no-functions]
#
# Notes:
# - Requires Firebase CLI: https://firebase.google.com/docs/cli
# - By default, vendors Python deps into functions/packages using uv (if available) or pip.

set -euo pipefail

PROJECT_ID=""
REGION="us-west1"
DEPLOY_HOSTING=1
DEPLOY_FUNCTIONS=1
SKIP_VENDOR=0
FORCE_TOOL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      PROJECT_ID="$2"; shift 2 ;;
    -r|--region)
      REGION="$2"; shift 2 ;;
    --skip-vendor)
      SKIP_VENDOR=1; shift ;;
    --use-uv)
      FORCE_TOOL="uv"; shift ;;
    --use-pip)
      FORCE_TOOL="pip"; shift ;;
    --no-hosting)
      DEPLOY_HOSTING=0; shift ;;
    --no-functions)
      DEPLOY_FUNCTIONS=0; shift ;;
    -h|--help)
      sed -n '1,40p' "$0"; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: --project <PROJECT_ID> is required" >&2
  exit 1
fi

# Sanity check CWD
if [[ ! -f "firebase.json" ]] || [[ ! -d "functions" ]]; then
  echo "Error: Run this script from the repo root (firebase.json not found)." >&2
  exit 1
fi

echo "==> Checking Firebase CLI"
if ! command -v firebase >/dev/null 2>&1; then
  echo "Firebase CLI not found. Install with: npm i -g firebase-tools" >&2
  exit 1
fi

FB_ARGS=(--project "$PROJECT_ID")
if [[ -n "${FIREBASE_TOKEN:-}" ]]; then
  FB_ARGS+=(--token "$FIREBASE_TOKEN")
fi

if [[ "$SKIP_VENDOR" -eq 0 ]]; then
  echo "==> Vendoring Python dependencies to functions/packages"
  mkdir -p functions/packages
  TOOL="$FORCE_TOOL"
  if [[ -z "$TOOL" ]]; then
    if command -v uv >/dev/null 2>&1; then
      TOOL="uv"
    elif command -v pip >/dev/null 2>&1; then
      TOOL="pip"
    else
      echo "Neither uv nor pip found; skipping vendoring. Ensure Firebase installs requirements." >&2
      SKIP_VENDOR=1
    fi
  fi
  if [[ "$SKIP_VENDOR" -eq 0 ]]; then
    if [[ "$TOOL" == "uv" ]]; then
      echo "> Using uv to vendor deps"
      uv pip install -r functions/requirements.txt --target functions/packages
    else
      echo "> Using pip to vendor deps"
      pip install -r functions/requirements.txt -t functions/packages
    fi
  fi
else
  echo "==> Skipping vendoring per flag"
fi

ONLY_ARGS=()
if [[ "$DEPLOY_FUNCTIONS" -eq 1 ]] && [[ "$DEPLOY_HOSTING" -eq 1 ]]; then
  ONLY_ARGS=(--only functions,hosting)
elif [[ "$DEPLOY_FUNCTIONS" -eq 1 ]]; then
  ONLY_ARGS=(--only functions)
elif [[ "$DEPLOY_HOSTING" -eq 1 ]]; then
  ONLY_ARGS=(--only hosting)
else
  echo "Nothing to deploy (both functions and hosting disabled)." >&2
  exit 1
fi

echo "==> Deploying to Firebase (region: $REGION)"
# Region is set in code via set_global_options; this is informational.
firebase deploy "${ONLY_ARGS[@]}" "${FB_ARGS[@]}"

echo "==> Done"
echo "Hosting endpoint:   https://$PROJECT_ID.web.app/mcp"
echo "Function endpoint:   https://$REGION-$PROJECT_ID.cloudfunctions.net/mcp_server/mcp"
