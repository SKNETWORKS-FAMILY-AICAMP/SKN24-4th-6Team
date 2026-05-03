set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/aigo-server}"
SERVICE_NAME="${SERVICE_NAME:-gunicorn}"

export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

cd "$APP_DIR"

echo "▶ [1/5] git: 최신 main 동기화"
# 로컬 변경(예: 로그/캐시)이 있어도 강제로 origin/main 에 맞춤
git fetch --all --prune
git reset --hard origin/main

echo "▶ [2/5] uv: 의존성 동기화"
uv sync --frozen

echo "▶ [3/5] Django: 마이그레이션"
uv run python manage.py migrate --noinput

echo "▶ [4/5] Django: 정적 파일 수집"
uv run python manage.py collectstatic --noinput

echo "▶ [5/5] systemd: ${SERVICE_NAME} 재시작"
sudo systemctl restart "${SERVICE_NAME}"

# 재시작 직후 상태 확인 — 실패하면 non-zero 반환되어 set -e 가 잡음
# `--quiet` 는 sudoers 규칙(`is-active gunicorn`) 과 패턴이 안 맞아 비번을 묻게 되므로 제외
sudo systemctl is-active "${SERVICE_NAME}" >/dev/null

echo "✓ 배포 완료 ($(git rev-parse --short HEAD))"
