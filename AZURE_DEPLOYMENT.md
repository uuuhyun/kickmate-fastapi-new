# Azure App Service 배포 가이드

K리그 AI 해설 FastAPI 서버의 Azure App Service 배포 기술 문서

---

## 1. 왜 Azure App Service를 선택했나?

- **PaaS 방식**: 서버 관리 없이 코드만 배포
- **자동 스케일링**: 트래픽에 따라 인스턴스 자동 조절
- **빠른 배포**: ZIP 파일 업로드만으로 배포 완료
- **HTTPS 자동**: SSL 인증서 자동 적용
- **비용 효율**: 사용한 만큼만 과금 (Free tier 가능)

---

## 2. 배포 구성

| 항목 | 설정 |
|------|------|
| Runtime | Python 3.10 (Linux) |
| WSGI Server | Gunicorn + UvicornWorker |
| Framework | FastAPI (비동기) |
| 배포 방식 | ZIP Deploy |

---

## 3. 핵심 설정

### Startup Command

```bash
pip install -r requirements.txt && gunicorn -k uvicorn.workers.UvicornWorker api.main:app --bind=0.0.0.0:8000 --timeout 120
```

| 옵션 | 설명 |
|------|------|
| `pip install -r requirements.txt` | 서버 시작 시 의존성 설치 |
| `-k uvicorn.workers.UvicornWorker` | FastAPI async 기능 지원 |
| `--bind=0.0.0.0:8000` | 모든 IP에서 8000번 포트 접근 허용 |
| `--timeout 120` | LLM 호출 시 긴 응답 시간 대응 (기본 30초 → 120초) |

### 환경 변수 (Application Settings)

| Name | 설명 |
|------|------|
| `RUNPOD_API_KEY` | RunPod API 인증 키 |
| `RUNPOD_ENDPOINT_URL` | RunPod LLM 엔드포인트 URL |
| `SPRING_WEBHOOK_URL` | Spring Backend 콜백 URL |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` - 배포 시 자동 빌드 활성화 |

---

## 4. 배포 프로세스

### Step 1: App Service 생성
- Azure Portal → App Services → Create
- Runtime stack: **Python 3.10**
- Operating System: **Linux**

### Step 2: 환경 변수 설정
- Configuration → Application settings
- 위 환경 변수 4개 추가

### Step 3: ZIP 배포
```bash
# Azure CLI 사용
az webapp deploy --resource-group <resource-group> --name <app-name> --src-path azure_deployment.zip --type zip
```
또는 Azure Portal → Deployment Center → ZIP Deploy

### Step 4: Startup Command 설정
- Configuration → General settings → Startup Command
- 위 명령어 입력

### Step 5: 배포 확인
- API 서버: `https://<app-name>.azurewebsites.net`
- Swagger 문서: `https://<app-name>.azurewebsites.net/docs`
- 로그: Log stream에서 실시간 확인

---

## 5. 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure App Service                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │  Gunicorn   │───>│  Uvicorn    │───>│    FastAPI      │  │
│  │  (WSGI)     │    │  (ASGI)     │    │   Application   │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                                        │
         │ HTTPS (자동)                           │ HTTP
         ↓                                        ↓
   ┌──────────┐                           ┌──────────────┐
   │  Client  │                           │   RunPod     │
   │ (Spring) │                           │  Serverless  │
   └──────────┘                           └──────────────┘
```

---

## 6. 트러블슈팅

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| Application Error | uvicorn/gunicorn 미설치 | Startup Command에 `pip install` 추가 |
| 패키지 설치 안됨 | ZIP 배포 후 빌드 미실행 | `SCM_DO_BUILD_DURING_DEPLOYMENT=true` 설정 |
| 타임아웃 에러 | 기본 타임아웃 30초 | `--timeout 120` 옵션 추가 |
| 502 Bad Gateway | 포트 바인딩 실패 | `--bind=0.0.0.0:8000` 확인 |

### 로그 확인 방법

1. **Azure Portal**: App Service → Log stream
2. **Azure CLI**:
   ```bash
   az webapp log tail --name <app-name> --resource-group <resource-group>
   ```

---

## 7. 장점 요약

| 장점 | 설명 |
|------|------|
| 관리 편의성 | 서버 OS, 패치, 보안 자동 관리 |
| 빠른 배포 | ZIP 업로드만으로 수 분 내 배포 |
| 확장성 | 트래픽 증가 시 자동 스케일링 |
| 보안 | HTTPS 자동, 환경 변수 암호화 저장 |
| 모니터링 | Application Insights 연동 가능 |
| CI/CD | GitHub Actions 연동 지원 |

---

**작성일**: 2026-01-11
