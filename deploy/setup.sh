set -euo pipefail

DOMAIN="${DOMAIN:-}"
REPO_URL="${REPO_URL:-}"
APP_DIR="/var/www/aigo-server"
DEPLOY_USER="deploy"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: sudo 또는 root 로 실행해야 합니다 (예: sudo ./setup.sh)" >&2
  exit 1
fi
if [ -z "${DOMAIN}" ] || [ -z "${REPO_URL}" ]; then
  echo "사용법: sudo DOMAIN=api.example.com REPO_URL=git@github.com:org/aigo-server.git ./setup.sh" >&2
  exit 1
fi

# -----------------------------------------------------------------------------
echo "▶ [1/7] 시스템 패키지 설치"
# -----------------------------------------------------------------------------
apt-get update -y
apt-get install -y --no-install-recommends \
  ca-certificates curl git build-essential pkg-config \
  libpq-dev libssl-dev \
  nginx certbot python3-certbot-nginx \
  ufw

# -----------------------------------------------------------------------------
echo "▶ [2/7] ${DEPLOY_USER} 유저 생성 + sudo 권한"
# -----------------------------------------------------------------------------
if ! id "${DEPLOY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi

# deploy 유저가 비밀번호 없이 systemctl restart/reload gunicorn 만 가능하도록
SUDOERS_FILE="/etc/sudoers.d/deploy-gunicorn"
cat > "${SUDOERS_FILE}" <<EOF
${DEPLOY_USER} ALL=(root) NOPASSWD: /bin/systemctl restart gunicorn, /bin/systemctl reload gunicorn, /bin/systemctl is-active gunicorn
EOF
chmod 440 "${SUDOERS_FILE}"
visudo -c -f "${SUDOERS_FILE}"

# -----------------------------------------------------------------------------
echo "▶ [3/7] uv 설치 (${DEPLOY_USER} home)"
# -----------------------------------------------------------------------------
sudo -u "${DEPLOY_USER}" -H bash -c '
  if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
'

# -----------------------------------------------------------------------------
echo "▶ [4/7] 앱 디렉토리 + git clone"
# -----------------------------------------------------------------------------
mkdir -p "${APP_DIR}"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"

if [ ! -d "${APP_DIR}/.git" ]; then
  sudo -u "${DEPLOY_USER}" -H git clone "${REPO_URL}" "${APP_DIR}"
else
  echo "  (이미 clone 됨, 건너뜀 — deploy.sh 가 이후 동기화)"
fi

# 정적/미디어 디렉토리 미리 생성 (nginx 가 alias 로 참조)
sudo -u "${DEPLOY_USER}" mkdir -p "${APP_DIR}/staticfiles" "${APP_DIR}/mediafiles"

# -----------------------------------------------------------------------------
echo "▶ [5/7] .env 안내"
# -----------------------------------------------------------------------------
if [ ! -f "${APP_DIR}/.env" ]; then
  cat <<MSG

  ─────────────────────────────────────────────────────────
  ⚠ .env 파일이 없습니다. 다음 명령으로 직접 작성하세요:

      sudo -u ${DEPLOY_USER} cp ${APP_DIR}/.env.example ${APP_DIR}/.env
      sudo -u ${DEPLOY_USER} nano ${APP_DIR}/.env

  최소한 다음 값들을 운영 값으로 교체:
      DJANGO_SECRET_KEY      (랜덤 50자 이상)
      DJANGO_DEBUG=False
      DJANGO_ALLOWED_HOSTS=${DOMAIN}
      DJANGO_CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
      DB_HOST=<RDS 엔드포인트>
      DB_PASSWORD=<RDS 비밀번호>
      AIGO_AI_BASE_URL, AIGO_AI_INTERNAL_API_KEY
      EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
  ─────────────────────────────────────────────────────────

MSG
fi

# -----------------------------------------------------------------------------
echo "▶ [6/7] systemd gunicorn.service 등록"
# -----------------------------------------------------------------------------
install -m 644 "${APP_DIR}/deploy/gunicorn.service" /etc/systemd/system/gunicorn.service
systemctl daemon-reload
systemctl enable gunicorn
# .env 가 있을 때만 실제 시작 시도 (없으면 EnvironmentFile 부재로 실패)
if [ -f "${APP_DIR}/.env" ]; then
  systemctl restart gunicorn
  systemctl is-active --quiet gunicorn && echo "  gunicorn: active" || echo "  gunicorn: inactive (logs: journalctl -u gunicorn -n 50)"
else
  echo "  .env 가 없어 gunicorn 시작은 건너뜀. .env 작성 후: sudo systemctl start gunicorn"
fi

# -----------------------------------------------------------------------------
echo "▶ [7/7] nginx vhost 등록 + 도메인 치환"
# -----------------------------------------------------------------------------
NGINX_CONF="/etc/nginx/sites-available/aigo-server"
sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "${APP_DIR}/deploy/nginx.conf" > "${NGINX_CONF}"
ln -sf "${NGINX_CONF}" /etc/nginx/sites-enabled/aigo-server
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# -----------------------------------------------------------------------------
cat <<MSG

✓ EC2 초기 세팅 완료

다음 단계:
  1) DNS A 레코드: ${DOMAIN}  →  $(curl -s ifconfig.me 2>/dev/null || echo "<EC2 EIP>")
  2) .env 작성 (위 안내 참고) 후: sudo systemctl restart gunicorn
  3) 첫 마이그레이션: cd ${APP_DIR} && sudo -u ${DEPLOY_USER} bash deploy/deploy.sh
  4) SSL 발급:        sudo certbot --nginx -d ${DOMAIN}
  5) 슈퍼유저 생성:    cd ${APP_DIR} && sudo -u ${DEPLOY_USER} uv run python manage.py createsuperuser
  6) GitHub Secrets 등록: EC2_HOST, EC2_USER=${DEPLOY_USER}, EC2_SSH_KEY (deploy 유저 ~/.ssh/authorized_keys 에 매칭되는 개인키)

MSG