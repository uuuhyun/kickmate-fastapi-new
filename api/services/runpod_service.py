"""
RunPod Serverless LLM 서비스
FastAPI -> RunPod LLM 통신 처리

Version: 1.0
"""

import os
import json
import httpx
from typing import List, Optional
from io import StringIO

# 상위 디렉토리의 system_prompts 임포트
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from system_prompts import get_system_prompt

# 환경 변수에서 RunPod 설정 로드
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_URL = os.getenv("RUNPOD_ENDPOINT_URL", "")


class RunPodService:
    """RunPod Serverless LLM 호출 서비스"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        self.api_key = api_key or RUNPOD_API_KEY
        self.endpoint_url = endpoint_url or RUNPOD_ENDPOINT_URL

        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY is required")
        if not self.endpoint_url:
            raise ValueError("RUNPOD_ENDPOINT_URL is required")

    def _build_raw_data_csv(self, raw_data: List[dict]) -> str:
        """
        raw_data를 CSV 형식 문자열로 변환 (토큰 수 절약)

        Args:
            raw_data: 액션 데이터 리스트 (보통 10개)
                     (Spring Backend의 'id' 필드가 포함되어 있어도 자동으로 무시됨)

        Returns:
            CSV 형식 문자열
        """
        # CSV 헤더 (포함할 컬럼만)
        # 주의: Spring Backend가 추가하는 'id' 필드(DB PK)는 의도적으로 제외됨
        #      LLM 해설 생성에 불필요한 필드는 토큰 절약을 위해 전송하지 않음
        columns = [
            "action_id", "period_id", "time_seconds", "result_name",
            "start_x", "start_y", "end_x", "end_y", "dx", "dy",
            "type_name", "player_name_ko", "team_name_ko_short",
            "position_name", "main_position"
        ]

        # 필드명 매핑 (camelCase -> snake_case 또는 원본)
        field_mapping = {
            "action_id": ["actionId", "action_id"],
            "period_id": ["periodId", "period_id"],
            "time_seconds": ["timeSeconds", "time_seconds"],
            "result_name": ["resultName", "result_name"],
            "start_x": ["startX", "start_x"],
            "start_y": ["startY", "start_y"],
            "end_x": ["endX", "end_x"],
            "end_y": ["endY", "end_y"],
            "dx": ["dx"],
            "dy": ["dy"],
            "type_name": ["typeName", "type_name"],
            "player_name_ko": ["playerNameKo", "player_name_ko"],
            "team_name_ko_short": ["teamNameKoShort", "team_name_ko_short"],
            "position_name": ["positionName", "position_name"],
            "main_position": ["mainPosition", "main_position"]
        }

        def get_value(item: dict, column: str) -> str:
            """아이템에서 컬럼 값 추출"""
            # 좌표 관련 컬럼 (소수점 2자리로 반올림하여 토큰 절약)
            coordinate_columns = {"start_x", "start_y", "end_x", "end_y", "dx", "dy"}

            for key in field_mapping.get(column, [column]):
                if key in item:
                    val = item[key]
                    if val is None:
                        return ""

                    # 좌표 컬럼은 소수점 2자리로 반올림
                    if column in coordinate_columns:
                        try:
                            val = round(float(val), 2)
                        except (ValueError, TypeError):
                            pass  # 변환 실패 시 원본 유지

                    # CSV 안전 처리 (쉼표, 따옴표 이스케이프)
                    val_str = str(val)
                    if "," in val_str or '"' in val_str or "\n" in val_str:
                        val_str = '"' + val_str.replace('"', '""') + '"'
                    return val_str
            return ""

        # CSV 생성
        lines = [",".join(columns)]  # 헤더

        for item in raw_data:
            row = [get_value(item, col) for col in columns]
            lines.append(",".join(row))

        return "\n".join(lines)

    def _build_match_info_text(self, match_info: dict) -> str:
        """
        match_info를 간결한 텍스트 형식으로 변환

        Args:
            match_info: 경기 메타데이터

        Returns:
            텍스트 형식 문자열
        """
        # 필드명 매핑
        field_mapping = {
            "gameId": ["gameId", "game_id"],
            "homeTeamNameKo": ["homeTeamNameKo", "home_team_name_ko"],
            "awayTeamNameKo": ["awayTeamNameKo", "away_team_name_ko"],
            "homeTeamNameKoShort": ["homeTeamNameKoShort", "home_team_name_ko_short"],
            "awayTeamNameKoShort": ["awayTeamNameKoShort", "away_team_name_ko_short"],
            "venue": ["venue"],
            "gameDate": ["gameDate", "game_date"],
            "weather": ["weather"],
            "temperature": ["temperature"],
            "homeTeamUniform": ["homeTeamUniform", "home_team_uniform"],
            "awayTeamUniform": ["awayTeamUniform", "away_team_uniform"],
            "referee": ["referee"],
            "assistantReferees": ["assistantReferees", "assistant_referees"],
            "fourthOfficial": ["fourthOfficial", "fourth_official"],
            "varReferees": ["varReferees", "var_referees"],
        }

        def get_val(key: str) -> str:
            for k in field_mapping.get(key, [key]):
                if k in match_info and match_info[k]:
                    return str(match_info[k])
            return "N/A"

        text = f"""경기ID: {get_val("gameId")}
홈팀: {get_val("homeTeamNameKo")} ({get_val("homeTeamNameKoShort")})
원정팀: {get_val("awayTeamNameKo")} ({get_val("awayTeamNameKoShort")})
경기장: {get_val("venue")}
날짜: {get_val("gameDate")}
날씨: {get_val("weather")}
기온: {get_val("temperature")}
홈팀유니폼: {get_val("homeTeamUniform")}
원정팀유니폼: {get_val("awayTeamUniform")}
주심: {get_val("referee")}
부심: {get_val("assistantReferees")}
제4심: {get_val("fourthOfficial")}
VAR 심판: {get_val("varReferees")}"""

        return text

    def build_user_prompt(
        self,
        match_info: dict,
        raw_data: List[dict]
    ) -> str:
        """
        사용자 프롬프트 생성 (system_prompts.py의 BASE_CONTEXT 기반)

        Args:
            match_info: 경기 메타데이터
            raw_data: 액션 데이터 (보통 10개)

        Returns:
            사용자 프롬프트 문자열
        """
        match_info_text = self._build_match_info_text(match_info)
        raw_data_csv = self._build_raw_data_csv(raw_data)

        # BASE_CONTEXT에 맞춘 프롬프트
        prompt = f"""# 경기 정보
{match_info_text}

# 액션 데이터 (CSV)
{raw_data_csv}

**중요: 위 {len(raw_data)}개 액션 모두에 대해 누락 없이 반드시 해설을 생성하세요.**
각 액션마다 한 문장으로 해설하여 총 {len(raw_data)}개의 JSON 객체를 배열로 반환하세요.
"""

        return prompt

    async def call_llm(
        self,
        style: str,
        match_info: dict,
        raw_data: List[dict],
        timeout: float = 300.0
    ) -> List[dict]:
        """
        RunPod LLM 호출

        Args:
            style: 해설 스타일 ("CASTER", "ANALYST", "FRIEND")
            match_info: 경기 메타데이터
            raw_data: 액션 데이터 (보통 10개)

        Returns:
            해설 스크립트 배열 (입력 액션 수와 동일)

        Raises:
            Exception: LLM 호출 실패 시
        """
        system_prompt = get_system_prompt(style)
        user_prompt = self.build_user_prompt(match_info, raw_data)

        # OpenAI Chat Completion API 형식
        # /openai/v1/chat/completions 엔드포인트는 표준 OpenAI 형식 사용
        payload = {
            "model": "skt/a.x-4.0-light",  # Colab 코드와 동일하게
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4096,  # 모델 컨텍스트 길이(8192) 초과 방지
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self.endpoint_url,
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                raise Exception(
                    f"RunPod API error: {response.status_code} - {response.text}"
                )

            result = response.json()

            # OpenAI 응답 구조 파싱
            if "error" in result:
                raise Exception(f"RunPod error: {result['error']}")

            # OpenAI Chat Completion 응답에서 텍스트 추출
            llm_response = self._extract_openai_text(result)

            # JSON 배열 파싱
            scripts = self._parse_llm_response(llm_response, raw_data)

            return scripts

    def _extract_openai_text(self, result: dict) -> str:
        """
        OpenAI Chat Completion 응답에서 텍스트 추출

        Args:
            result: OpenAI API 응답

        Returns:
            LLM 텍스트 응답

        Raises:
            Exception: 응답 파싱 실패 시
        """
        try:
            # OpenAI 표준 형식: result["choices"][0]["message"]["content"]
            choices = result.get("choices", [])
            if not choices:
                raise Exception("응답에 choices가 없습니다")

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                raise Exception("응답에 content가 없습니다")

            return content

        except Exception as e:
            raise Exception(f"OpenAI 응답 파싱 실패: {e}")

    def _extract_llm_text(self, output) -> str:
        """
        RunPod 응답에서 LLM 텍스트 추출 (다양한 형식 지원) - Legacy
        주의: /runsync 엔드포인트용, /openai/v1 엔드포인트는 _extract_openai_text() 사용

        Args:
            output: RunPod API 응답의 output 필드

        Returns:
            LLM 텍스트 응답
        """
        # output이 문자열인 경우
        if isinstance(output, str):
            return output

        # output이 리스트인 경우 (SKT A.X 모델 형식)
        # [{'choices': [{'tokens': ['텍스트']}], 'usage': {...}}]
        if isinstance(output, list) and len(output) > 0:
            first_item = output[0]
            if isinstance(first_item, dict):
                # choices 추출
                choices = first_item.get("choices", [])
                if choices and isinstance(choices, list):
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        # tokens 추출
                        tokens = first_choice.get("tokens", [])
                        if tokens and isinstance(tokens, list):
                            return "".join(str(t) for t in tokens)
                        # text 추출 (다른 형식)
                        text = first_choice.get("text", "")
                        if text:
                            return text
                        # message 추출 (OpenAI 호환 형식)
                        message = first_choice.get("message", {})
                        if isinstance(message, dict):
                            return message.get("content", "")

        # output이 dict인 경우
        if isinstance(output, dict):
            # text 필드
            if "text" in output:
                return output["text"]
            # response 필드
            if "response" in output:
                return output["response"]
            # content 필드
            if "content" in output:
                return output["content"]
            # choices 필드 (OpenAI 형식)
            choices = output.get("choices", [])
            if choices and isinstance(choices, list):
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message", {})
                    if isinstance(message, dict):
                        return message.get("content", "")
                    return first_choice.get("text", "")

        # 최후의 수단: 문자열 변환
        return str(output)

    def _save_prompt_to_file(
        self,
        system_prompt: str,
        user_prompt: str,
        style: str
    ) -> None:
        """
        LLM에 입력되는 프롬프트를 파일로 저장 (디버깅용)

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            style: 해설 스타일
        """
        from datetime import datetime
        import json

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompt_{timestamp}.txt"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        content = f"""{'=' * 80}
LLM 입력 프롬프트
{'=' * 80}
스타일: {style}
생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'=' * 80}
[System Prompt]
{'=' * 80}
{system_prompt}

{'=' * 80}
[User Prompt]
{'=' * 80}
{user_prompt}

{'=' * 80}
[Full Messages (OpenAI Format)]
{'=' * 80}
{json.dumps(messages, ensure_ascii=False, indent=2)}
"""

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] 프롬프트가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"[WARNING] 프롬프트 저장 실패: {e}")

    def _save_runpod_response(self, result: dict) -> None:
        """
        RunPod 응답을 JSON 파일로 저장 (디버깅용)

        Args:
            result: RunPod API 응답
        """
        from datetime import datetime
        import json

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"runpod_response_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"[OK] RunPod 응답이 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"[WARNING] RunPod 응답 저장 실패: {e}")

    def _parse_llm_response(
        self,
        llm_response: str,
        raw_data: List[dict]
    ) -> List[dict]:
        """
        LLM 응답에서 JSON 배열 파싱

        Args:
            llm_response: LLM 텍스트 응답
            raw_data: 원본 액션 데이터 (fallback용)

        Returns:
            파싱된 스크립트 배열
        """
        # JSON 배열 추출 시도
        llm_response = llm_response.strip()

        # JSON 블록 찾기 (```json ... ``` 형식)
        if "```json" in llm_response:
            start = llm_response.find("```json") + 7
            end = llm_response.find("```", start)
            if end > start:
                llm_response = llm_response[start:end].strip()
        elif "```" in llm_response:
            start = llm_response.find("```") + 3
            end = llm_response.find("```", start)
            if end > start:
                llm_response = llm_response[start:end].strip()

        # [ 로 시작하지 않으면 찾기
        if not llm_response.startswith("["):
            bracket_start = llm_response.find("[")
            if bracket_start != -1:
                llm_response = llm_response[bracket_start:]

        # ] 로 끝나지 않으면 찾기
        if not llm_response.endswith("]"):
            bracket_end = llm_response.rfind("]")
            if bracket_end != -1:
                llm_response = llm_response[:bracket_end + 1]

        try:
            scripts = json.loads(llm_response)

            # 유효성 검사 및 정규화
            validated_scripts = []
            for script in scripts:
                validated_scripts.append({
                    "actionId": str(script.get("actionId", "")),
                    "timeSeconds": str(script.get("timeSeconds", "")),
                    "tone": script.get("tone", "DEFAULT"),
                    "description": script.get("description", "")
                })

            return validated_scripts

        except json.JSONDecodeError as e:
            # 파싱 실패 시 기본 응답 생성
            print(f"JSON 파싱 실패: {e}")
            print(f"LLM 응답: {llm_response[:500]}...")

            # Fallback: 원본 데이터 기반 기본 스크립트 생성
            return self._generate_fallback_scripts(raw_data)

    def _generate_fallback_scripts(self, raw_data: List[dict]) -> List[dict]:
        """
        LLM 응답 파싱 실패 시 기본 스크립트 생성

        Args:
            raw_data: 원본 액션 데이터

        Returns:
            기본 스크립트 배열
        """
        field_mapping = {
            "actionId": ["actionId", "action_id"],
            "timeSeconds": ["timeSeconds", "time_seconds"],
            "typeName": ["typeName", "type_name"],
            "playerNameKo": ["playerNameKo", "player_name_ko"],
        }

        def get_val(item: dict, key: str) -> str:
            for k in field_mapping.get(key, [key]):
                if k in item:
                    return str(item[k]) if item[k] else ""
            return ""

        scripts = []
        for item in raw_data:
            action_id = get_val(item, "actionId")
            time_seconds = get_val(item, "timeSeconds")
            type_name = get_val(item, "typeName")
            player_name = get_val(item, "playerNameKo")

            description = f"{player_name} 선수가 {type_name}을 합니다." if player_name and type_name else "플레이 진행 중입니다."

            scripts.append({
                "actionId": action_id,
                "timeSeconds": time_seconds,
                "tone": "DEFAULT",
                "description": description
            })

        return scripts


# 싱글톤 인스턴스
_runpod_service: Optional[RunPodService] = None


def get_runpod_service() -> RunPodService:
    """RunPod 서비스 인스턴스 반환"""
    global _runpod_service
    if _runpod_service is None:
        _runpod_service = RunPodService()
    return _runpod_service
