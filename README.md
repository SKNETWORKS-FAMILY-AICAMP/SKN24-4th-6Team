# aigo-web

[SKN24] LLM Chatbot Service '아이고 청년' 배포용 서버

Django 6 / Python 3.12. Companion server to the [`aigo-ai`](../aigo-ai) RAG chatbot.

---

## 프로젝트 구조

```
aigo-web/
  manage.py
  config/                    # 프로젝트 패키지 (settings/urls/wsgi/asgi)
    settings/
      base.py                # 공통 설정 — django-environ으로 .env에서 로드
      dev.py                 # 개발 (DEBUG=True, manage.py 기본값)
      prod.py                # 운영 (wsgi/asgi 기본값)
      test.py                # 테스트 (pytest 기본값)
    urls.py
    wsgi.py
    asgi.py
  accounts/                  # Custom User (AbstractUser stub) + JWT 엔드포인트
  health/                    # 예제 앱: GET /healthz
  chat/                      # Thread/Message + aigo-ai 프록시
  core/                      # 공유 추상 모델 (TimestampedModel) — INSTALLED_APPS 미등록
  pyproject.toml             # uv + ruff + pytest 설정
  uv.lock                    # 의존성 진실 (lockfile)
  requirements.txt           # uv export 산출물 — pip 사용자 무마찰
  requirements-dev.txt       # 동일, dev 그룹
  .env.example               # 환경 변수 템플릿
```

각 앱은 자기 자신만 책임집니다 (`apps.py`/`models.py`/`urls.py`/`views.py`/`tests/`).
앱 간 직접 import는 최소화 — 공유 로직은 `core/`에 둡니다.

---

## 시작하기

### uv (권장)

```bash
uv sync                                       # .venv 동기화
cp .env.example .env.local                    # 환경 변수 채우기
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
                                              # → DJANGO_SECRET_KEY 값으로 .env.local에 붙여넣기
uv run python manage.py migrate
uv run python manage.py runserver
uv run pytest                                 # 테스트 (config.settings.test)
```

### pip (uv 미설치 시)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env.local
python manage.py migrate
python manage.py runserver
pytest
```

`/healthz`가 `{"status":"ok"}`를 반환하면 부트스트랩 성공입니다.

---

## 환경 변수

`.env.example`이 모든 키를 안전한 placeholder로 정의합니다. `.env.local`(개발) 또는 `.env.prod`(운영)으로 복사 후 채우세요. 두 파일 모두 gitignored — 절대 커밋 금지.

| 키 | 용도 | 비고 |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | 설정 모듈 | dev/prod/test |
| `DJANGO_SECRET_KEY` | Django 시크릿 키 | prod에서 미설정 시 raise |
| `DJANGO_DEBUG` | 디버그 플래그 | `env.bool` (`True`/`False`) |
| `DJANGO_ALLOWED_HOSTS` | 허용 호스트 | csv |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | CSRF 신뢰 오리진 | csv, prod 필수 |
| `DATABASE_URL` | DB URL | psycopg 3 → `postgresql+psycopg://...` |
| `DJANGO_JWT_SIGNING_KEY` | JWT 서명 키 | 미설정 시 `DJANGO_SECRET_KEY` 사용 |
| `AIGO_AI_BASE_URL` | aigo-ai (FastAPI) base URL | 기본 `http://localhost:8000` |
| `DJANGO_TIME_ZONE` | 타임존 | 기본 `Asia/Seoul` |
| `DJANGO_LANGUAGE_CODE` | 로케일 | 기본 `ko-kr` |

---

## 새 앱 추가

1. 톱레벨 `<name>/` 디렉터리 생성, 다음 파일 추가:
   - `__init__.py`
   - `apps.py` — `name = "<name>"` (단일 세그먼트라 `label` 불필요)
   - `models.py`, `views.py`, `urls.py` (필요한 만큼)
   - `migrations/__init__.py`
   - `tests/__init__.py` (필수 — 모듈명 충돌 방지), `tests/test_*.py`
2. `config/settings/base.py`의 `LOCAL_APPS`에 `"<name>"` 추가
3. `config/urls.py`에서 라우팅 필요 시 `include("<name>.urls")`
4. `pyproject.toml`의 `[tool.pytest.ini_options].testpaths`에 `"<name>"` 추가
5. `uv run python manage.py makemigrations <name>`

---

## requirements 재생성 (의존성 변경 시)

`uv.lock`이 진실, `requirements*.txt`는 산출물입니다. `pyproject.toml`에서 의존성을 추가/변경했다면:

```bash
uv lock                                                              # uv.lock 갱신
uv export --no-hashes --no-annotate --no-dev -o requirements.txt
uv export --no-hashes --no-annotate --only-group dev -o requirements-dev.txt
```

세 파일을 함께 커밋하세요. CI에서 drift 검사를 추가하는 것을 권장합니다.

---

## 커맨드 치트시트

| 명령 | uv | pip |
|---|---|---|
| 마이그레이션 | `uv run python manage.py migrate` | `python manage.py migrate` |
| 슈퍼유저 | `uv run python manage.py createsuperuser` | `python manage.py createsuperuser` |
| 개발 서버 | `uv run python manage.py runserver` | `python manage.py runserver` |
| 테스트 | `uv run pytest` | `pytest` |
| 린트 | `uv run ruff check .` | `ruff check .` |
| 포맷 | `uv run ruff format .` | `ruff format .` |
| 운영 체크 | `DJANGO_SETTINGS_MODULE=config.settings.prod uv run python manage.py check --deploy` | 동일 (uv 제외) |

---

## 컨벤션

- **들여쓰기 2칸** (sibling `aigo-ai/`와 동일). Ruff `indent-width=2`로 강제.
- **커밋 메시지**: `<type>: <설명>` (영문 type, 한국어 설명). 타입: `feat | fix | docs | refactor | chore | style | perf | ci`.
- **`.env.local` / `.env.prod` 절대 커밋 금지.** 새 env 키 추가 시 같은 커밋에 `.env.example`도 갱신.