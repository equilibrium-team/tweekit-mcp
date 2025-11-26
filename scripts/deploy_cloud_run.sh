#!/usr/bin/env bash
# Build the TweekIT MCP container and deploy to Cloud Run.
#
# Usage:
#   bash scripts/deploy_cloud_run.sh <local|stage|prod> --version <x.y.z> [options]
# Options:
#   --project <PROJECT_ID>        Google Cloud project (default: active gcloud config or tweekitmcp-a26b6)
#   --region <REGION>             Cloud Run region (default: us-west1)
#   --env-file <PATH>             Optional env vars file (YAML for Cloud Run, dotenv for local docker)
#   --image-repo <REPO>           Container repo (default: gcr.io/PROJECT/tweekit-mcp)
#   --service-stage <NAME>        Override stage service name (default: tweekit-mcp-stage)
#   --service-prod <NAME>         Override prod service name (default: tweekit-mcp-prod)
#   --no-allow-unauthenticated    Skip --allow-unauthenticated flag
#   --skip-build                  Deploy existing image (requires --image-uri)
#   --image-uri <URI>             Full image URI; implies --skip-build unless overridden
#   --local-port <PORT>           Exposed port for local docker run (default: 8080)
#   --no-run                      For local target, build image but skip docker run
#   -h|--help                     Show this help message

set -euo pipefail

function usage() {
  sed -n '1,20p' "$0"
}

if [[ $# -lt 1 ]]; then
  echo "Error: deployment target (local|stage|prod) is required." >&2
  usage
  exit 1
fi

TARGET="$1"
shift

case "$TARGET" in
  local|stage|prod) ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    echo "Error: unknown target '$TARGET' (expected local, stage, or prod)." >&2
    exit 1
    ;;
esac

PROJECT_ID=""
REGION="us-west1"
VERSION=""
ENV_FILE=""
IMAGE_REPO=""
IMAGE_URI=""
ALLOW_UNAUTH=1
SERVICE_STAGE="tweekit-mcp-stage"
SERVICE_PROD="tweekit-mcp-prod"
SKIP_BUILD=0
LOCAL_PORT=8080
RUN_LOCAL=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_ID="$2"; shift 2 ;;
    --region)
      REGION="$2"; shift 2 ;;
    --version)
      VERSION="$2"; shift 2 ;;
    --env-file)
      ENV_FILE="$2"; shift 2 ;;
    --image-repo)
      IMAGE_REPO="$2"; shift 2 ;;
    --image-uri)
      IMAGE_URI="$2"; SKIP_BUILD=1; shift 2 ;;
    --service-stage)
      SERVICE_STAGE="$2"; shift 2 ;;
    --service-prod)
      SERVICE_PROD="$2"; shift 2 ;;
    --no-allow-unauthenticated)
      ALLOW_UNAUTH=0; shift ;;
    --skip-build)
      SKIP_BUILD=1; shift ;;
    --local-port)
      LOCAL_PORT="$2"; shift 2 ;;
    --no-run)
      RUN_LOCAL=0; shift ;;
    -h|--help)
      usage
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1 ;;
  esac
done

case "$TARGET" in
  local)
    SERVICE_NAME="tweekit-mcp-local"
    ;;
  stage)
    SERVICE_NAME="$SERVICE_STAGE"
    ;;
  prod)
    SERVICE_NAME="$SERVICE_PROD"
    ;;
esac

if [[ "$TARGET" == "local" ]]; then
  if [[ -z "$VERSION" ]]; then
    VERSION="local"
  fi

  if [[ -z "$IMAGE_REPO" ]]; then
    IMAGE_REPO="tweekit-mcp-local"
  fi

  if [[ -z "$IMAGE_URI" ]]; then
    IMAGE_URI="${IMAGE_REPO}:${VERSION}"
  fi

  if [[ ! -f "Dockerfile" ]]; then
    echo "Error: Dockerfile not found; run from repo root." >&2
    exit 1
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker CLI not found; required for local deployments." >&2
    exit 1
  fi

  if [[ "$SKIP_BUILD" -eq 0 ]]; then
    echo "==> Building local container image: ${IMAGE_URI}"
    docker build -t "$IMAGE_URI" .
  else
    echo "==> Skipping docker build (using image: ${IMAGE_URI})"
  fi

  if [[ "$RUN_LOCAL" -eq 1 ]]; then
    DOCKER_ARGS=(-p "${LOCAL_PORT}:8080")
    if [[ -n "$ENV_FILE" ]]; then
      DOCKER_ARGS+=(--env-file "$ENV_FILE")
    fi
    echo "==> Running container locally on port ${LOCAL_PORT}"
    echo "    docker run --rm ${DOCKER_ARGS[*]} ${IMAGE_URI}"
    docker run --rm "${DOCKER_ARGS[@]}" "$IMAGE_URI"
  else
    echo "==> Skipping docker run (image available at ${IMAGE_URI})"
  fi
  exit 0
fi

if [[ -z "$PROJECT_ID" ]]; then
  if command -v gcloud >/dev/null 2>&1; then
    PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
    if [[ "$PROJECT_ID" == "(unset)" ]]; then
      PROJECT_ID=""
    fi
  fi
fi

if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID="tweekitmcp-a26b6"
fi

if [[ -z "$VERSION" ]] && [[ "$SKIP_BUILD" -eq 0 ]] && [[ -z "$IMAGE_URI" ]]; then
  echo "Error: --version is required when building a new image." >&2
  exit 1
fi

if [[ -z "$IMAGE_REPO" ]]; then
  IMAGE_REPO="gcr.io/${PROJECT_ID}/tweekit-mcp"
fi

if [[ -z "$IMAGE_URI" ]]; then
  IMAGE_URI="${IMAGE_REPO}:${VERSION}"
fi

if [[ ! -f "Dockerfile" ]]; then
  echo "Error: Dockerfile not found; run from repo root." >&2
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud CLI is not installed or not on PATH." >&2
  exit 1
fi

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  echo "==> Building container image: ${IMAGE_URI}"
  gcloud builds submit \
    --project "$PROJECT_ID" \
    --tag "$IMAGE_URI" \
    .
else
  echo "==> Skipping build step (using image: ${IMAGE_URI})"
fi

DEPLOY_ARGS=(
  "$SERVICE_NAME"
  --project "$PROJECT_ID"
  --image "$IMAGE_URI"
  --region "$REGION"
  --platform managed
)

if [[ -n "$ENV_FILE" ]]; then
  DEPLOY_ARGS+=(--env-vars-file "$ENV_FILE")
fi

if [[ "$ALLOW_UNAUTH" -eq 1 ]]; then
  DEPLOY_ARGS+=(--allow-unauthenticated)
fi

echo "==> Deploying service '${SERVICE_NAME}' to region '${REGION}' (project: ${PROJECT_ID})"
gcloud run deploy "${DEPLOY_ARGS[@]}"

echo "==> Deployment complete"
echo "Service: ${SERVICE_NAME}"
echo "Image:   ${IMAGE_URI}"
