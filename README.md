# K리그 AI 해설 FastAPI 서버

RunPod Serverless LLM을 사용한 K리그 실시간 AI 해설 생성 FastAPI 백엔드

## 관련 링크

- **발표자료**: [킥메이트_발표자료.pdf](https://github.com/uuuhyun/kickmate-fastapi/blob/main/%ED%82%A5%EB%A9%94%EC%9D%B4%ED%8A%B8_%EB%B0%9C%ED%91%9C%EC%9E%90%EB%A3%8C.pdf)
- **시연영상**: [DACON 코드 공유](https://dacon.io/competitions/official/236648/codeshare/13759)
- **프론트엔드 (React + Vite)**: [seohyun1257/Kickmate](https://github.com/seohyun1257/Kickmate)
- **백엔드 (Spring)**: [luna111122/kickmate](https://github.com/luna111122/kickmate)

## 프로젝트 개요

시각장애인, 라디오 청취자, 축구 입문자를 위한 **배리어프리 AI 해설 서비스**의 백엔드 API입니다.
On-ball Event 데이터를 분석하여 10개 액션에 대한 실시간 해설을 생성합니다.

### 주요 특징

✅ **접근성 우선**: 시각적으로 경기를 보지 못하는 사용자를 위한 명확하고 구체적인 위치 묘사
✅ **비동기 Job 처리**: 요청 즉시 응답 후 백그라운드에서 LLM 호출
✅ **Spring Backend 연동**: Webhook + 폴링 하이브리드 방식 지원
✅ **3가지 해설 스타일**: CASTER (역동적), ANALYST (분석적), FRIEND (친근함)
✅ **7가지 감정 톤**: DEFAULT, EXCITED, ANGRY, SAD, CALM, QUESTION, EMPHASIS
✅ **토큰 최적화**: CSV 형식 + 좌표 소수점 2자리로 약 40% 토큰 절감
✅ **완전성 보장**: 10개 액션 모두에 대한 해설 누락 없이 생성

## 프로젝트 구조

```
open_track2/
├── api/                          # FastAPI 서버
│   ├── main.py                   # FastAPI 애플리케이션
│   ├── models/
│   │   └── schemas.py            # Pydantic 데이터 모델
│   ├── routers/
│   │   └── commentary.py         # 해설 생성 API + Webhook
│   └── services/
│       ├── job_store.py          # 작업 상태 관리 (In-memory)
│       └── runpod_service.py     # RunPod LLM 통신 (OpenAI 호환 형식)
├── system_prompts.py             # LLM 시스템 프롬프트 (접근성 중심)
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경 변수 템플릿
├── .gitignore                    # Git 제외 목록
├── README.md                     # 프로젝트 설명
├── API_SPEC.md                   # API 명세서
├── API_IO_FORMAT.md              # 입출력 형식 상세
└── WEBHOOK_FORMAT.md             # Webhook 페이로드 명세
```

**참고**: `data/` 디렉토리(대용량 CSV 파일)는 GitHub에 포함되지 않습니다. 별도로 관리해야 합니다.

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

주요 패키지:
- `fastapi` - 웹 프레임워크
- `uvicorn` - ASGI 서버
- `httpx` - HTTP 클라이언트 (RunPod, Webhook 통신)
- `pydantic` - 데이터 검증
- `python-dotenv` - 환경 변수 관리
- `gunicorn` - WSGI 서버 (운영 환경용)

### 2. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일에 다음 항목을 설정하세요 (`.env.example` 참조):

- `RUNPOD_API_KEY`: RunPod API 키 ([RunPod 콘솔](https://www.runpod.io/)에서 발급)
- `RUNPOD_ENDPOINT_URL`: RunPod 엔드포인트 URL (**OpenAI 호환 형식** 사용 필수: `/openai/v1/chat/completions`)
- `API_HOST`: FastAPI 서버 호스트 (기본값: `0.0.0.0`)
- `API_PORT`: FastAPI 서버 포트 (기본값: `8000`)
- `SPRING_WEBHOOK_URL`: Spring Backend 콜백 엔드포인트 URL (선택 사항)

자세한 형식은 [.env.example](.env.example) 파일을 참조하세요.

### 3. 서버 실행

```bash
# 개발 모드 (자동 재로드)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 운영 모드
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

서버가 시작되면:
- API 서버: http://localhost:8000
- Swagger 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc

## API 사용법

### 해설 생성 요청 (Spring → FastAPI)

```bash
POST http://fastapi-서버:8000/ai/commentary/jobs
Content-Type: application/json
```

**요청 Body**:
```json
{
  "gameId": "126283",
  "style": "CASTER",
  "matchInfo": {
    "game_id": 126283,
    "home_team_name_ko": "울산 HD FC",
    "away_team_name_ko": "포항 스틸러스",
    "home_team_name_ko_short": "울산",
    "away_team_name_ko_short": "포항",
    "venue": "문수월드컵경기장",
    "game_date": "2024-03-01 14:00:00",
    "weather": "맑음",
    "temperature": "3.0°C",
    "home_team_uniform": "파란색 홈유니폼",
    "away_team_uniform": "흰색 원정유니폼",
    "referee": "김우성",
    "assistant_referees": "김계용,박상준",
    "fourth_official": "송민석",
    "var_referees": "채상협,강동호"
  },
  "rawData": [
    {
      "action_id": 0,
      "period_id": 1,
      "time_seconds": 0.667,
      "result_name": "Successful",
      "start_x": 52.42,
      "start_y": 33.49,
      "end_x": 31.32,
      "end_y": 38.27,
      "dx": -21.1,
      "dy": 4.79,
      "type_name": "Pass",
      "player_name_ko": "아타루",
      "team_name_ko_short": "울산",
      "position_name": "CAM",
      "main_position": "CAM"
    }
    // ... 총 10개 액션
  ]
}
```

**즉시 응답**:
```json
{
  "jobId": "job_82f395",
  "status": "PENDING"
}
```

### Webhook 콜백 (FastAPI → Spring)

작업 완료 시 FastAPI가 자동으로 Spring Backend에 POST 요청을 보냅니다:

**성공 시**:
```json
POST http://spring-server:8080/ai/callback/ai-result
{
  "jobId": "job_82f395",
  "gameId": "126283",
  "status": "DONE",
  "script": [
    {
      "actionId": "0",
      "timeSeconds": "0.667",
      "tone": "DEFAULT",
      "description": "아타루 선수가 중앙에서 왼쪽으로 패스를 시도합니다."
    }
    // ... 10개
  ]
}
```

**실패 시**:
```json
{
  "jobId": "job_82f395",
  "gameId": "126283",
  "status": "ERROR",
  "errorCode": "LLM_TIMEOUT",
  "errorMessage": "Request timeout after 120 seconds"
}
```

### 작업 상태 조회 (폴링 백업)

Webhook 실패 대비 폴링 방식도 지원합니다:

```bash
GET http://fastapi-서버:8000/ai/commentary/jobs/{jobId}
```

자세한 내용은 [API_SPEC.md](API_SPEC.md), [WEBHOOK_FORMAT.md](WEBHOOK_FORMAT.md)를 참조하세요.

## 해설 스타일

### CASTER (캐스터형)
- 존댓말 사용
- 역동적이고 빠른 템포
- 감정 표현 풍부
- 긴장감 있는 해설

### ANALYST (분석가형)
- 존댓말 사용
- 차분하고 침착한 톤
- 위치와 거리 구체적 언급
- 전술적 분석 포함

### FRIEND (친구형)
- 반말 사용
- 친근하고 편안한 톤
- 쉬운 표현 사용
- 전문 용어 최소화
- 감탄사 활용

## 감정 톤 (AI 자동 생성)

| Tone | 사용 상황 | 예시 |
|------|----------|------|
| DEFAULT | 일반 플레이 | 패스, 드리블, Pass Received |
| EXCITED | 골 기회, 슈팅 | Shot, 페널티 박스 진입 |
| ANGRY | 파울, 반칙 | Foul, Yellow Card |
| SAD | 실책, 실점 | Unsuccessful Pass, 골 허용 |
| CALM | 안전 빌드업 | 수비 지역 패스, GK 소유 |
| QUESTION | 불확실 상황 | Offside 판정 대기 |
| EMPHASIS | 중요 순간 | 결정적 찬스, 역전 골 |

AI가 액션의 맥락(위치, 타입, 결과)을 분석하여 자동으로 적절한 tone을 선택합니다.

## 시스템 프롬프트 특징

### 접근성 중심 설계

- **시각적으로 보지 못하는 청취자**를 위한 명확한 위치 및 방향 묘사
- **지시 대명사 금지**: "이쪽", "저기" 같은 표현 사용 안 함
- **명확한 주어**: 누가, 어디로, 무엇을 했는지 구체적으로 설명
- **팀명/유니폼 언급**: 가끔씩 팀 정보를 언급하여 청취자 이해 돕기
- **좌표 숫자 사용 금지**: 숫자 좌표나 미터 수치를 절대 언급하지 않고, 자연스러운 위치 표현만 사용
- **포지션 언급**: 중요한 순간에 가끔씩 선수 포지션을 자연스럽게 언급

### 좌표 시스템 명확화

- 필드: 105m(가로) × 68m(세로)
- 홈팀: 왼쪽→오른쪽 공격 (x=0 → x=105)
- 원정팀: 오른쪽→왼쪽 공격 (x=105 → x=0)
- **필드 구역**:
  - x=0~52.5: 홈팀 수비 지역, 원정팀 공격 지역
  - x=52.5~105: 홈팀 공격 지역, 원정팀 수비 지역

### 완전성 보장

- **10개 액션 모두** 해설 생성 필수
- 누락 없이 배열 길이 일치 보장
- 각 액션마다 한 문장으로 해설

## 성능 최적화

### 1. CSV 형식 전송
JSON 대비 약 30-40% 토큰 절감:
```csv
action_id,period_id,time_seconds,start_x,start_y,end_x,end_y,...
0,1,0.667,52.42,33.49,31.32,38.27,...
```

### 2. 좌표 반올림
소수점 2자리로 제한하여 토큰 추가 절감:
- 변경 전: `52.418205` (9자)
- 변경 후: `52.42` (5자)
- 10개 액션 기준: 약 100-120 토큰 절감

### 3. 비동기 처리
- 요청 즉시 응답 (Spring Backend 대기 최소화)
- 백그라운드에서 LLM 호출
- In-memory Job Store로 빠른 상태 관리

## 아키텍처

### Webhook + 폴링 하이브리드 방식

```
   [AWS EC2]                            [Azure App Service]
┌─────────────┐                     ┌─────────────────────────────┐
│   Spring    │  ① POST /jobs       │       FastAPI Server        │
│  Backend    │────────────────────>│  ┌───────────────────────┐  │
│             │    (10 actions)     │  │     Job Store         │  │
└─────────────┘                     │  │   (In-memory Dict)    │  │
       ↑                            │  └───────────────────────┘  │
       │      ② jobId: PENDING      │             │               │
       │      (즉시 응답)            │             ↓               │
       │                            │     ③ LLM 호출 (백그라운드)   │
       │                            └─────────────────────────────┘
       │                                          │
       │                                          ↓
       │                            ┌─────────────────────────────┐
       │                            │    RunPod Serverless (GPU)  │
       │                            │  ┌───────────────────────┐  │
       │         ④ 10개 해설 생성    │  │    vLLM (Serving)     │  │
       │         (tone+description) │  │  ┌─────────────────────────────┐  │  │
       │                            │  │  │EXAONE-3.5-7.8B-Instruct│  │  │
       │                            │  │  └─────────────────────────────┘  │  │
       │                            │  └───────────────────────┘  │
       │                            └─────────────────────────────┘
       │                                          │
       │         ⑤ Webhook 전송                    │
       └──────────────────────────────────────────┘
            POST /ai/callback/ai-result
            (자동, 백업: 폴링 GET /jobs/{id})
```

## 운영 환경 배포

### Docker 배포 (권장)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t kleague-ai-api .
docker run -d -p 8000:8000 --env-file .env kleague-ai-api
```

### Azure App Service 배포 (권장)

Azure App Service를 사용한 PaaS 배포 방법입니다.

#### 1. Azure Portal에서 App Service 생성

- Runtime stack: **Python 3.10**
- Operating System: **Linux**

#### 2. 환경 변수 설정

Azure Portal → App Service → Configuration → Application settings에서 다음 환경 변수 추가:

| Name | Value |
|------|-------|
| `RUNPOD_API_KEY` | RunPod API 키 |
| `RUNPOD_ENDPOINT_URL` | RunPod 엔드포인트 URL |
| `SPRING_WEBHOOK_URL` | Spring Backend Webhook URL |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

#### 3. ZIP 배포

```bash
# 배포 파일 준비 (api/, system_prompts.py, requirements.txt 등)
# azure_deployment.zip 생성 후 Azure Portal에서 업로드

# 또는 Azure CLI 사용
az webapp deploy --resource-group <resource-group> --name <app-name> --src-path azure_deployment.zip --type zip
```

#### 4. Startup Command 설정

Azure Portal → App Service → Configuration → General settings → Startup Command:

```bash
pip install -r requirements.txt && gunicorn -k uvicorn.workers.UvicornWorker api.main:app --bind=0.0.0.0:8000 --timeout 120
```

#### 5. 배포 확인

- API 서버: `https://<app-name>.azurewebsites.net`
- Swagger 문서: `https://<app-name>.azurewebsites.net/docs`
- 로그 확인: Azure Portal → App Service → Log stream

---

### AWS EC2 배포

```bash
# 패키지 설치
sudo apt update
sudo apt install python3-pip python3-venv

# 가상환경 설정
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Gunicorn 실행 (requirements.txt에 포함됨)
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Systemd 서비스 등록

`/etc/systemd/system/kleague-ai.service`:

```ini
[Unit]
Description=K-League AI Commentary API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/open_track2
Environment="PATH=/home/ubuntu/open_track2/venv/bin"
ExecStart=/home/ubuntu/open_track2/venv/bin/gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable kleague-ai
sudo systemctl start kleague-ai
```

## 에러 처리

### 주요 에러 코드

| 코드 | 설명 | 대응 방법 |
|------|------|----------|
| `LLM_TIMEOUT` | RunPod API 타임아웃 (300초) | RunPod 상태 확인, 재시도 |
| `LLM_ERROR` | LLM 호출 실패 | API 키 확인, 엔드포인트 확인 |
| `INVALID_DATA` | 입력 데이터 유효성 오류 | 요청 형식 확인 |
| `JOB_NOT_FOUND` | 존재하지 않는 Job ID | jobId 재확인 |

## 트러블슈팅

### RunPod 연결 실패

```bash
# 1. 환경 변수 확인
cat .env | grep RUNPOD

# 2. 네트워크 연결 확인
curl -I https://api.runpod.ai

# 3. API 키 유효성 확인
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/health
```

### Webhook 전송 실패

서버 로그 확인:
```
[WEBHOOK] 웹훅 전송 실패 (Spring 서버가 꺼져있나요?): ...
```

→ Spring Backend 서버 상태 및 URL 확인

### 응답이 계속 PENDING

1. RunPod 엔드포인트 상태 확인
2. 서버 로그에서 `[DEBUG]` 메시지 확인
3. Job Store 상태 확인: `GET /ai/commentary/jobs`

## 문서

- [API_SPEC.md](API_SPEC.md) - API 상세 명세
- [API_IO_FORMAT.md](API_IO_FORMAT.md) - 입출력 형식 상세
- [WEBHOOK_FORMAT.md](WEBHOOK_FORMAT.md) - Webhook 페이로드 명세

## 라이선스

이 프로젝트는 K리그 배리어프리 AI 해설 프로젝트의 일부입니다.

---

**버전**: 2.1
**최종 업데이트**: 2026-01-11