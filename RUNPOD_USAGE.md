# RunPod Serverless LLM 활용 가이드

K리그 AI 해설 프로젝트의 RunPod Serverless 활용 방식

---

## 1. RunPod Serverless 선택 이유

### 왜 RunPod인가?

| 장점 | 설명 |
|------|------|
| **GPU 서버리스** | 사용한 만큼만 과금, 서버 관리 불필요 |
| **오픈소스 LLM 지원** | HuggingFace 모델 자유롭게 선택 가능 |
| **vLLM 통합** | 고성능 추론 서빙 프레임워크 내장 |
| **OpenAI 호환 API** | 표준 API 형식으로 쉬운 통합 |
| **Auto Scaling** | 요청량에 따라 자동 확장 |

---

## 2. 기술 스택

### 계층 구조

```
┌─────────────────────────────────────┐
│  RunPod Serverless (GPU)            │  ← 인프라 (GPU 서버)
│  ┌───────────────────────────────┐  │
│  │    vLLM (Serving)             │  │  ← 서빙 프레임워크 (추론 최적화)
│  │  ┌─────────────────────────┐  │  │
│  │  │EXAONE-3.5-7.8B-Instruct │  │  │  ← LLM 모델 (7.8B급)
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

| 구성 요소 | 역할 |
|----------|------|
| **EXAONE-3.5-7.8B-Instruct** | LG AI Research에서 공개한 LLM (한국어 성능 우수) |
| **vLLM** | 페이지드 어텐션 기반 고속 추론 서빙 |
| **RunPod Serverless** | GPU 자원 관리 및 Auto Scaling |

---

## 3. API 통신 방식

### OpenAI 호환 형식 사용

RunPod는 OpenAI ChatCompletion API와 동일한 형식을 지원합니다.

```python
# Endpoint URL (OpenAI 호환)
https://api.runpod.ai/v2/{endpoint_id}/openai/v1/chat/completions

# 요청 형식
{
  "model": "lgai-exaone/exaone-3.5-7.8b-instruct",
  "messages": [
    {"role": "system", "content": "시스템 프롬프트"},
    {"role": "user", "content": "사용자 프롬프트"}
  ],
  "max_tokens": 4096,
  "temperature": 0.7,
  "top_p": 0.9
}
```

### FastAPI에서 호출

```python
import httpx

async def call_runpod_llm(system_prompt: str, user_prompt: str):
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            RUNPOD_ENDPOINT_URL,
            headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
            json={
                "model": "skt/a.x-4.0-light",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 4096,
                "temperature": 0.7
            }
        )
        return response.json()
```

---

## 4. 프롬프트 최적화

### CSV 형식 전송

JSON 대신 CSV 형식으로 전송하여 **토큰 30-40% 절감**

**Before (JSON):**
```json
{
  "actions": [
    {
      "action_id": 0,
      "start_x": 52.418205,
      "start_y": 33.491873,
      "type_name": "Pass"
    }
  ]
}
```
→ 약 120 토큰

**After (CSV):**
```csv
action_id,start_x,start_y,type_name
0,52.42,33.49,Pass
```
→ 약 70 토큰 (**42% 절감**)

### 좌표 반올림

소수점 2자리로 제한하여 추가 토큰 절감
- `52.418205` → `52.42`
- 10개 액션 기준: **100-120 토큰 추가 절감**

---

## 5. 실제 워크플로우

```
FastAPI Server                          RunPod Serverless
─────────────────                       ─────────────────
     │
     │  ① 10개 액션 데이터 받음
     ├─────────────────────────────────────────────┐
     │                                             │
     │  ② System Prompt 생성                        │
     │     (CASTER/ANALYST/FRIEND)                 │
     │                                             │
     │  ③ User Prompt 생성 (CSV 형식)                │
     │     - matchInfo (경기 정보)                   │
     │     - rawData (10개 액션, CSV)               │
     │                                             │
     ├─────────────────────────────────────────────┘
     │
     │  ④ POST /openai/v1/chat/completions
     ├────────────────────────────────────────────>
     │                                             │
     │                                        vLLM 추론
     │                                             │
     │                                    skt/A.X-4.0-Light
     │                                             │
     │  ⑤ Response (10개 해설 JSON)                 │
     │<────────────────────────────────────────────┤
     │                                             │
     │  ⑥ 파싱 & 검증                               │
     │     - tone 추출                              │
     │     - description 추출                       │
     │     - 10개 완전성 확인                        │
     │                                             │
     │  ⑦ Webhook → Spring Backend                 │
     └─────────────────────────────────────────────>
```

---

## 6. 성능 최적화

### vLLM의 핵심 기술

| 기술 | 효과 |
|------|------|
| **Paged Attention** | GPU 메모리 효율 2배 향상 |
| **Continuous Batching** | 처리량 10-20배 증가 |
| **KV Cache 최적화** | 긴 컨텍스트 처리 성능 향상 |

### 우리 프로젝트 적용 결과

- **응답 시간**: 10개 액션 기준 평균 20-30초
- **토큰 효율**: CSV 형식으로 입력 토큰 40% 절감
- **비용 효율**: Serverless로 사용한 만큼만 과금

---

## 7. 환경 설정

### RunPod 엔드포인트 설정

1. RunPod Console → Serverless → Create Endpoint
2. Template 선택: **vLLM** (OpenAI 호환)
3. Model 입력: `skt/a.x-4.0-light`
4. GPU 선택: NVIDIA A40 (또는 더 높은 사양)
5. Workers: Auto Scaling 설정

### FastAPI 환경 변수

```bash
# .env 파일
RUNPOD_API_KEY=rpa_xxxxxxxxxxxxxxxxxxxxx
RUNPOD_ENDPOINT_URL=https://api.runpod.ai/v2/{endpoint_id}/openai/v1/chat/completions
```

---

## 8. 장점 요약

| 항목 | 기존 방식 (직접 GPU 관리) | RunPod Serverless |
|------|-------------------------|------------------|
| 초기 비용 | 높음 (GPU 서버 구매) | 없음 |
| 운영 비용 | 고정 비용 | 사용량 기반 과금 |
| 서버 관리 | 필요 (OS, 드라이버 등) | 불필요 |
| 확장성 | 수동 | 자동 |
| vLLM 설정 | 직접 구성 필요 | 내장 템플릿 제공 |
| 배포 속도 | 수일 | 수 분 |

---

**작성일**: 2026-01-11
