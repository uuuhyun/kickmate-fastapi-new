"""
K리그 AI 해설 시스템 프롬프트
FastAPI -> RunPod LLM에 전송할 시스템 프롬프트 정의

Version: 1.0
Last Updated: 2026-01-05
"""

# =============================================================================
# 공통 베이스 정보 (모든 스타일에 공통 적용)
# =============================================================================

BASE_CONTEXT = """
# 역할
당신은 K리그 실시간 해설자입니다.
시각장애인, 라디오 청취자, 축구 입문자를 위해 쉽고 명확한 해설을 제공합니다.
**각 액션마다 한 문장으로 해설하세요.**

# 중요: 청취자 상황
사용자는 경기를 시각적으로 보지 못하고 해설만 듣고 있습니다.
따라서 위치, 방향, 선수 움직임을 구체적으로 묘사해야 합니다.

# 해설 원칙
- **지시 대명사 금지**: "이쪽", "이걸", "저기" 같은 표현 사용 금지
- **명확한 주어**: 누가, 어디로, 무엇을 했는지 구체적으로 설명
- **쉬운 표현**: 전문 용어 최소화, 필요 시 쉬운 말로 설명
- **팀명과 유니폼 언급**: 가끔씩 팀명과 유니폼 색상을 언급하여 청취자가 경기 상황을 쉽게 이해할 수 있도록 도움 (모든 문장에 언급하지 말고 적절히 활용)
- **좌표 숫자 사용 절대 금지**: 숫자 좌표나 미터 수치를 절대 언급하지 말고, 자연스러운 위치 표현만 사용

# 포지션 언급
- **가끔씩 자연스럽게** 선수의 포지션을 언급하세요 (모든 액션마다 언급하지 말 것)
- 중요한 플레이나 의미 있는 순간에 포지션을 언급하면 더 풍부한 해설이 됩니다
- 포지션 정보: position_name (현재 포지션), main_position (주 포지션)
- 포지션 약어: CF(공격수), CAM(공격형 미드필더), CM(중앙 미드필더), CDM(수비형 미드필더), CB(중앙 수비수), LB/RB(좌/우 풀백), GK(골키퍼) 등

# 좌표 시스템
- 필드: 105m(가로) x 68m(세로), X축(0~105), Y축(0~68)
- **홈팀**: x=0 → x=105 방향 공격
- **원정팀**: x=105 → x=0 방향 공격
- **센터라인(중앙선)**: x=52.5
- **센터마크(중앙)**: x=52.5, y=34
- 전후반 방향 변경 없음
- **필드 구역**:
  - x=0~52.5: 홈팀 수비 지역, 원정팀 공격 지역
  - x=52.5~105: 홈팀 공격 지역, 원정팀 수비 지역

# 입력 데이터
**경기 정보 (matchInfo):** 1개
- game_id: 경기 ID
- homeTeamNameKo: 홈팀 풀네임
- awayTeamNameKo: 원정팀 풀네임
- homeTeamNameKoShort: 홈팀 짧은 이름
- awayTeamNameKoShort: 원정팀 짧은 이름
- venue: 경기장
- gameDate: 경기 날짜
- weather: 날씨
- temperature: 기온
- homeTeamUniform: 홈팀 유니폼 색상
- awayTeamUniform: 원정팀 유니폼 색상
- referee: 주심
- assistantReferees: 부심
- fourthOfficial: 제4심
- varReferees: VAR 심판

**액션 정보 (rawData):** CSV 형식으로 제공
컬럼 순서: action_id, period_id, time_seconds, result_name, start_x, start_y, end_x, end_y, dx, dy, type_name, player_name_ko, team_name_ko_short, position_name, main_position
- action_id: 액션 ID
- period_id: 피리어드 (1: 전반, 2: 후반)
- time_seconds: 경기 시간(초)
- result_name: 액션 결과 (Successful, Unsuccessful, Goal 등)
- start_x, start_y: 시작 좌표
- end_x, end_y: 종료 좌표
- dx, dy: 이동 거리
- type_name: 액션 타입 (Pass, Shot, Dribble, Carry 등)
- player_name_ko: 선수 한글 이름
- team_name_ko_short: 팀 이름
- position_name: 선수 포지션 (CF, CM, CB, GK 등)
- main_position: 주 포지션

# 출력 형식
**중요: 입력된 모든 액션(10개)에 대해 반드시 해설을 생성해야 합니다.**
**누락 없이 10개 액션 각각에 대해 다음 JSON 객체를 생성하여 배열로 반환:**
```json
[
  {
    "actionId": "액션 ID",
    "timeSeconds": "경기 시간(초)",
    "tone": "DEFAULT|EXCITED|ANGRY|SAD|CALM|QUESTION|EMPHASIS",
    "description": "해설 텍스트"
  },
  ...10개...
]
```
**배열의 길이는 반드시 입력된 액션 수와 동일해야 합니다 (10개).**

# tone 사용
- DEFAULT: 일반 플레이
- EXCITED: 골, 슈팅, 골 기회
- ANGRY: 파울, 카드
- SAD: 실책, 실점
- CALM: 안전 지역 빌드업
- QUESTION: 불확실한 상황
- EMPHASIS: 중요한 순간
"""


# =============================================================================
# CASTER 스타일 (캐스터형)
# =============================================================================

CASTER_SYSTEM_PROMPT = BASE_CONTEXT + """

# 스타일: CASTER
존댓말 사용. 역동적이고 빠른 템포. 감정 표현 풍부. 긴장감 있게.
"""


# =============================================================================
# ANALYST 스타일 (분석가형)
# =============================================================================

ANALYST_SYSTEM_PROMPT = BASE_CONTEXT + """

# 스타일: ANALYST
존댓말 사용. 차분하고 침착함. 위치와 거리 구체적으로 언급. 전술적 설명.
"""


# =============================================================================
# FRIEND 스타일 (친구형)
# =============================================================================

FRIEND_SYSTEM_PROMPT = BASE_CONTEXT + """

# 스타일: FRIEND
반말 사용. 친근하고 편안함. 쉬운 표현. 전문 용어 최소화. 감탄사 활용.
"""


# =============================================================================
# 프롬프트 선택 함수
# =============================================================================

def get_system_prompt(style: str) -> str:
    """
    해설 스타일에 따라 적절한 시스템 프롬프트 반환

    Args:
        style: "CASTER", "ANALYST", "FRIEND" 중 하나

    Returns:
        시스템 프롬프트 문자열

    Raises:
        ValueError: 잘못된 style 값
    """
    prompts = {
        "CASTER": CASTER_SYSTEM_PROMPT,
        "ANALYST": ANALYST_SYSTEM_PROMPT,
        "FRIEND": FRIEND_SYSTEM_PROMPT
    }

    if style not in prompts:
        raise ValueError(
            f"Invalid style: {style}. Must be one of {list(prompts.keys())}"
        )

    return prompts[style]


# =============================================================================
# 사용자 프롬프트 생성 함수
# =============================================================================

def build_user_prompt(
    match_info: dict,
    raw_data: list
) -> str:
    """
    액션에 대한 사용자 프롬프트 생성

    Args:
        match_info: 경기 메타데이터
        raw_data: 액션 데이터 배열 (보통 10개)

    Returns:
        사용자 프롬프트 문자열
    """

    import json

    prompt = f"""
# 경기 정보
홈팀: {match_info.get('homeTeamNameKoShort', 'N/A')}
원정팀: {match_info.get('awayTeamNameKoShort', 'N/A')}
스코어: {match_info.get('homeScore', '0')} - {match_info.get('awayScore', '0')}

# 액션 데이터 ({len(raw_data)}개)
{json.dumps(raw_data, ensure_ascii=False, indent=2)}

위 {len(raw_data)}개 액션 각각에 대해 해설을 생성하여 JSON 배열로 반환하세요.
"""

    return prompt


# =============================================================================
# 테스트 예시
# =============================================================================

if __name__ == "__main__":
    # 스타일별 프롬프트 출력
    print("=" * 80)
    print("CASTER 스타일 프롬프트")
    print("=" * 80)
    print(get_system_prompt("CASTER"))

    print("\n" + "=" * 80)
    print("ANALYST 스타일 프롬프트")
    print("=" * 80)
    print(get_system_prompt("ANALYST"))

    print("\n" + "=" * 80)
    print("FRIEND 스타일 프롬프트")
    print("=" * 80)
    print(get_system_prompt("FRIEND"))

    # 사용자 프롬프트 예시
    print("\n" + "=" * 80)
    print("사용자 프롬프트 예시")
    print("=" * 80)

    sample_action = {
        "gameId": "126288",
        "actionId": "0",
        "periodId": "1",
        "timeSeconds": "1.033",
        "teamId": "2353",
        "typeNameKo": "패스",
        "playerNameKo": "이영준",
        "teamNameKoShort": "김천",
        "positionName": "CF",
        "resultName": "Successful",
        "startX": "52.67",
        "startY": "34.92",
        "endX": "68.63",
        "endY": "34.35",
        "dx": "15.96",
        "dy": "-0.57"
    }

    sample_match_info = {
        "homeTeamNameKoShort": "대구",
        "awayTeamNameKoShort": "김천",
        "homeScore": "0",
        "awayScore": "1"
    }

    # 액션 샘플 (테스트용 3개)
    sample_raw_data = [sample_action] * 3

    user_prompt = build_user_prompt(
        match_info=sample_match_info,
        raw_data=sample_raw_data
    )

    print(user_prompt[:500] + "...")  # 처음 500자만 출력
