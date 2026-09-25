#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/martaxi-boss/lowcost-europa}"
RUNNER_VERSION="${RUNNER_VERSION:-2.337.0}"
RUNNER_SHA256="${RUNNER_SHA256:-70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613}"
RUNNER_USER="${RUNNER_USER:-github-runner}"
RUNNER_LABELS="${RUNNER_LABELS:-martaxi-vps,lowcost-europa}"
INSTALL_DIR="${INSTALL_DIR:-/opt/actions-runner/lowcost-europa}"
RUNNER_NAME="${RUNNER_NAME:-martaxi-vps-$(hostname -s)}"

: "${RUNNER_TOKEN:?Set RUNNER_TOKEN to the short-lived registration token from GitHub Settings > Actions > Runners > New self-hosted runner.}"

if [ "$(uname -s)" != "Linux" ]; then
  echo "ERROR: this bootstrap is for Linux only." >&2
  exit 1
fi

case "$(uname -m)" in
  x86_64|amd64) ARCH="x64" ;;
  *)
    echo "ERROR: unsupported architecture: $(uname -m). This packet is pinned for Linux x64." >&2
    exit 1
    ;;
esac

ASSET="actions-runner-linux-${ARCH}-${RUNNER_VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${ASSET}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if ! id "${RUNNER_USER}" >/dev/null 2>&1; then
  sudo useradd --create-home --shell /bin/bash "${RUNNER_USER}"
fi

sudo mkdir -p "${INSTALL_DIR}"
sudo chown "${RUNNER_USER}:${RUNNER_USER}" "${INSTALL_DIR}"

if [ -f "${INSTALL_DIR}/.runner" ]; then
  echo "ERROR: a GitHub runner is already configured in ${INSTALL_DIR}; refusing to overwrite it." >&2
  exit 1
fi

curl -fL --retry 3 --retry-delay 2 "${URL}" -o "${TMP_DIR}/${ASSET}"
printf '%s  %s\n' "${RUNNER_SHA256}" "${TMP_DIR}/${ASSET}" | sha256sum -c -

sudo -u "${RUNNER_USER}" tar -xzf "${TMP_DIR}/${ASSET}" -C "${INSTALL_DIR}"

if [ -x "${INSTALL_DIR}/bin/installdependencies.sh" ]; then
  sudo "${INSTALL_DIR}/bin/installdependencies.sh"
fi

sudo -u "${RUNNER_USER}" env \
  REPO_URL="${REPO_URL}" \
  RUNNER_TOKEN="${RUNNER_TOKEN}" \
  RUNNER_NAME="${RUNNER_NAME}" \
  RUNNER_LABELS="${RUNNER_LABELS}" \
  INSTALL_DIR="${INSTALL_DIR}" \
  bash -c 'cd "$INSTALL_DIR" && ./config.sh --unattended --url "$REPO_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --labels "$RUNNER_LABELS" --work _work'

cd "${INSTALL_DIR}"
sudo ./svc.sh install "${RUNNER_USER}"
sudo ./svc.sh start
sudo ./svc.sh status

echo "SELF_HOSTED_RUNNER_BOOTSTRAP=PASS"
echo "RUNNER_NAME=${RUNNER_NAME}"
echo "RUNNER_LABELS=${RUNNER_LABELS}"
