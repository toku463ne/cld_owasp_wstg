#!/usr/bin/env bash
# WSTG 原文をピン留めバージョンで取得する。
#   ./scripts/fetch_wstg.sh              # v4.2 の Markdown 原文（既定・推奨）
#   ./scripts/fetch_wstg.sh --html-mirror # 公開サイトの HTML ミラー（任意）
#
# 取得物は docs/owasp/ に置かれ、.gitignore により追跡されない。
set -euo pipefail

WSTG_VERSION="4.2"
WSTG_TAG="v${WSTG_VERSION}"
TARBALL_URL="https://codeload.github.com/OWASP/wstg/tar.gz/refs/tags/${WSTG_TAG}"
MIRROR_URL="https://owasp.org/www-project-web-security-testing-guide/stable/"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${REPO_ROOT}/docs/owasp"
MODE="${1:-source}"

mkdir -p "${DEST}"

fetch_source() {
  local target="${DEST}/wstg-${WSTG_VERSION}"
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' RETURN

  echo "[fetch_wstg] WSTG ${WSTG_TAG} (Markdown) を取得: ${TARBALL_URL}"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${TARBALL_URL}" -o "${tmp}/wstg.tar.gz"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "${tmp}/wstg.tar.gz" "${TARBALL_URL}"
  else
    echo "[fetch_wstg] curl か wget が必要です" >&2
    exit 1
  fi

  tar -xzf "${tmp}/wstg.tar.gz" -C "${tmp}"
  local extracted="${tmp}/wstg-${WSTG_VERSION}"
  [ -d "${extracted}" ] || extracted="$(find "${tmp}" -maxdepth 1 -type d -name 'wstg-*' | head -n1)"

  rm -rf "${target}"
  mv "${extracted}" "${target}"

  # 参考：SHA256 を記録しておくと再現性を検証できる
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${tmp}/wstg.tar.gz" | awk '{print $1}' > "${target}/.tarball.sha256" || true
  fi

  echo "[fetch_wstg] 完了: ${target}"
  echo "[fetch_wstg] テスト本体: ${target}/document/4-Web_Application_Security_Testing/"
}

fetch_html_mirror() {
  command -v wget >/dev/null 2>&1 || { echo "[fetch_wstg] wget が必要です" >&2; exit 1; }
  echo "[fetch_wstg] HTML ミラーを取得: ${MIRROR_URL}"
  ( cd "${DEST}" && wget \
      --mirror --convert-links --adjust-extension --page-requisites --no-parent \
      --no-host-directories --cut-dirs=1 \
      --reject-regex '.*(donate|membership|sitemap).*' \
      "${MIRROR_URL}" )
  echo "[fetch_wstg] 完了: ${DEST}/stable/"
}

case "${MODE}" in
  source|--source) fetch_source ;;
  --html-mirror|html) fetch_html_mirror ;;
  -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
  *) echo "[fetch_wstg] 不明な引数: ${MODE}" >&2; exit 2 ;;
esac

cat <<'MSG'

次の手順:
  python scripts/build_wstg_index.py   # matrix/wstg_tests.yaml を再生成
  python scripts/gen_playbooks.py      # playbooks/ のカードを再生成
MSG
