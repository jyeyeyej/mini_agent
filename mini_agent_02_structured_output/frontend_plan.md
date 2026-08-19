# 2-4. 카카오맵 구조화 여행 추천 — Frontend Plan

## 1. 목적과 범위

`mini_agent_02_structured_output`의 Streamlit 프론트엔드에 **2-4. 카카오맵 여행 추천** 페이지를 추가한다.

사용자가 여행지, 여행 기간, 원하는 활동을 자연어로 입력하면 프론트엔드는 백엔드의 구조화 여행 추천 API를 호출한다. 성공 응답을 바탕으로 여행 기간, 카카오맵 마커, 랜드마크, 음식·예상 가격, 주의사항, 원본 JSON을 표시한다.

이 계획의 구현 범위는 프론트엔드로 한정한다. LLM 호출, Pydantic Schema, Provider 처리, API Router와 테스트는 백엔드 담당 범위다.

### 포함

- 사이드바에 `2-4. 카카오맵 여행 추천` 메뉴 추가
- Streamlit 입력·로딩·결과·오류 UI
- 백엔드 API Client 호출
- 카카오맵 JavaScript SDK를 이용한 지도·마커 렌더링
- 지도 실패와 텍스트 결과 표시의 분리

### 제외

- 백엔드 파일, API Router, Provider, Pydantic Schema 변경
- 카카오 로컬 검색 API를 통한 장소·좌표 검증
- 예약, 결제, 길찾기, 실시간 교통 정보
- 사용자 로그인과 추천 결과 저장
- 기존 2-1~2-3 페이지 기능 변경

## 2. 백엔드 연동 계약

프론트엔드는 아래 API가 백엔드에 구현되어 있다는 전제에서 동작한다.

```text
POST /api/structured/map-travel
Content-Type: application/json
```

### 요청

```json
{
  "provider": "mock",
  "message": "부산에 2박 3일 여행을 가고자 해. 관광지와 음식을 추천해 주세요."
}
```

- `provider`: `mock`, `gemini`, `openai`, `ollama`
- `message`: 공백이 아닌 자연어 여행 요청

### 성공 응답에서 사용할 필드

```json
{
  "provider": "mock",
  "model": "deterministic-map-travel-mock",
  "content": {
    "destination": "부산",
    "nights": 2,
    "days": 3,
    "summary": "해운대와 광안리를 중심으로 둘러보는 2박 3일 여행입니다.",
    "landmarks": [
      {
        "name": "해운대해수욕장",
        "description": "해변 산책과 바다 풍경을 즐길 수 있는 장소입니다.",
        "latitude": 35.1587,
        "longitude": 129.1604,
        "category": "beach"
      }
    ],
    "foods": [
      {
        "name": "돼지국밥",
        "estimated_price_krw": 10000,
        "description": "부산을 대표하는 따뜻한 국밥입니다.",
        "latitude": 35.1631,
        "longitude": 129.1635
      }
    ],
    "cautions": ["가격과 영업시간은 방문 전에 확인하세요."]
  },
  "latency_ms": 0
}
```

- `422`, `502` 응답 시 `detail`을 사용자용 오류 메시지로 표시한다.
- API가 준비되기 전에는 화면이 백엔드 연결 오류를 표시한다. 프론트는 임의의 Mock 데이터를 생성하지 않는다.

## 3. 수정·추가 파일

| 파일 | 작업 |
| --- | --- |
| `frontend/app_pages/12_map_travel.py` | 신규 Streamlit 페이지: 입력, API 호출, 결과 표시 |
| `frontend/core/kakao_map.py` | 신규 지도 HTML 생성 모듈 |
| `frontend/clients/map_travel_client.py` | 신규 전용 API Client |
| `frontend/app.py` | 페이지 등록 및 사이드바 메뉴 1개 추가 |

기존 `frontend/clients/agent_client.py`는 변경하지 않고, 기능 전용 Client를 분리한다.

## 4. 페이지 UI 및 사용자 흐름

```text
제목·안내
  ↓
Provider 선택 + 여행 요청 입력
  ↓
여행 추천 생성 버튼
  ↓
로딩 표시 → POST /api/structured/map-travel
  ↓
여행 기간·요약 → 카카오맵 → 랜드마크 → 음식/가격 → 주의사항 → 원본 JSON
```

### 입력 영역

- 제목: `🗺️ 카카오맵 여행 추천`
- Provider: `st.selectbox`로 `mock`, `gemini`, `openai`, `ollama` 선택
- 질문: `st.text_area`
- 실행: `st.button("여행 추천 생성")`
- Cloud Provider 선택 시 비용 발생 가능성을 안내한다.

### 결과 영역

- `destination`, `summary`, `model`, `latency_ms`를 표시한다.
- `nights=0`, `days=1`은 `당일치기`로 표시한다.
- 그 외에는 `N박 M일` 형식으로 표시한다.
- 랜드마크는 이름, 카테고리, 설명을 카드 또는 컨테이너로 표시한다.
- 음식은 이름, 예상 가격(천 단위 구분 기호 포함), 설명을 표 또는 카드로 표시한다.
- 주의사항은 `st.warning` 또는 목록으로 표시한다.
- 디버깅·학습 확인을 위해 성공 응답의 `content`를 `st.json`으로 표시한다.

## 5. 카카오맵 컴포넌트

`frontend/core/kakao_map.py`는 `st.components.v1.html()`에 전달할 HTML을 생성한다.

### 지도 렌더링 규칙

- `KAKAO_MAP_JAVASCRIPT_KEY` 환경변수로 JavaScript SDK를 로드한다.
- 위도·경도가 유효한 랜드마크와 음식만 마커로 만든다.
- 랜드마크와 음식은 다른 마커 색상 또는 아이콘으로 구분한다.
- 마커 클릭 시 이름과 설명을 InfoWindow로 표시한다.
- 유효한 마커가 여러 개이면 `LatLngBounds`로 전체 위치가 보이도록 맞춘다.
- 유효 마커가 없으면 지도 대신 안내 문구를 표시한다.
- SDK 로드 또는 초기화 실패 시 컴포넌트 내부 오류 문구를 표시한다.

### 안전한 데이터 전달

- API 응답 문자열을 JavaScript 코드에 직접 연결하지 않는다.
- 마커 데이터는 `json.dumps()`로 직렬화하여 HTML에 전달한다.
- `</script>` 같은 문자열이 코드로 해석되지 않도록 직렬화 결과를 안전하게 처리한다.
- 지도 HTML에는 JavaScript 키만 포함한다. OpenAI·Gemini·Ollama 관련 비밀 값은 포함하지 않는다.

## 6. 환경 설정과 카카오 개발자 콘솔

- 환경 변수명: `KAKAO_MAP_JAVASCRIPT_KEY`
- 카카오 개발자 콘솔에서는 **JavaScript 키**를 사용한다.
- 로컬 개발용 Web 플랫폼 도메인으로 `http://localhost:8501`을 등록한다.
- 배포 시에는 실제 배포 Origin을 별도로 등록한다.
- REST API 키나 Admin 키를 지도 HTML에 사용하지 않는다.

키가 없으면 지도 대신 `카카오맵 JavaScript 키가 설정되지 않았습니다.` 경고를 표시하고, 백엔드에서 받은 텍스트 결과는 계속 표시한다.

## 7. 오류 및 빈 상태 처리

| 상황 | 프론트 동작 |
| --- | --- |
| 백엔드 연결 실패 | `st.error`로 연결 오류 표시, 이전 결과는 렌더링하지 않음 |
| API 422/502 | 응답의 `detail`을 오류 메시지로 표시 |
| 카카오맵 키 없음 | 지도 경고만 표시, 랜드마크·음식·JSON은 유지 |
| SDK 또는 지도 초기화 실패 | 지도 영역의 오류 문구만 표시, 텍스트 결과는 유지 |
| 유효 좌표 없음 | 지도 대신 안내 문구, 목록은 유지 |
| 일부 좌표가 잘못됨 | 해당 위치 마커만 생략, 목록은 유지 |
| 음식 목록이 비어 있음 | `추천 음식이 없습니다.` 빈 상태 표시 |

## 8. 구현 순서

1. 백엔드 담당자와 `/api/structured/map-travel` 요청·응답 계약을 확인한다.
2. `map_travel_client.py`에 전용 호출 함수를 추가한다.
3. `kakao_map.py`에 안전한 HTML·마커 렌더링 함수를 구현한다.
4. `12_map_travel.py`에 입력, 버튼, 로딩, 결과 및 오류 UI를 구현한다.
5. `app.py`에서 페이지를 등록하고 2-3 아래에 사이드바 메뉴를 추가한다.
6. `mock` Provider의 성공 응답으로 전체 흐름을 확인한다.
7. 키 없음·지도 실패·빈 목록·API 오류 상태를 확인한다.
8. 기존 Streamlit 페이지가 정상적으로 열리는지 확인한다.

## 9. 완료 조건

- `streamlit run frontend/app.py`로 2-4 페이지에 접근할 수 있다.
- 사용자는 Provider와 자연어 여행 요청을 입력하고 버튼으로 API를 호출할 수 있다.
- API 성공 시 여행 기간, 지도, 랜드마크, 음식 가격, 주의사항, JSON이 표시된다.
- 당일치기는 `당일치기`, 숙박 여행은 `N박 M일`로 표시된다.
- 지도 마커와 텍스트 목록의 장소 데이터가 일치한다.
- 지도 키·SDK·좌표 문제가 발생해도 텍스트 결과는 유지된다.
- 기존 2-1~2-3 Streamlit 기능에 변경이 없다.
