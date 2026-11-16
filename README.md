# 🚗 EZ_LOAD_Algorithm

> **A\* 및 가중치 다익스트라 기반 초보 운전자 맞춤형 "쉬운 길" 라우팅 알고리즘 엔진**

운전이 미숙한 초보 운전자에게는 '가장 빠른 최단 경로'보다 '심리적 부담이 적은 안전하고 편안한 경로'가 필요합니다.  
**EZ_LOAD_Algorithm**은 도로 환경의 난이도 요소를 다각도로 수치화한 비용 모델을 설계하여, 조금 돌아가더라도 안심하고 주행할 수 있는 **"가장 쉬운 길(Easy Route)"**과 **"가장 빠른 길(Fast Route)"**을 함께 계산하고 비교해 주는 라우팅 엔진입니다.

---

## 📌 주요 특징

1. **15가지 도로 난이도 가중치 모델 (Cost Model)**
   * 유턴, 비보호 좌회전, 회전교차로, 좁은 골목길, 급커브, 합류·분기 등 초보자가 기피하는 도로 특성을 비용으로 환산
2. **개인 맞춤형 가중치 반영 (Personalized Context)**
   * 사용자의 운전 성향(특정 기피 요소, 고속도로 선호도)에 따라 실시간으로 가중치가 조정되는 적응형 탐색
3. **결정론적 고속 탐색 알고리즘**
   * LLM의 환각(Hallucination) 위험을 원천 차단하고, 빠른 응답 속도를 보장하기 위해 다익스트라 / A* 기반으로 설계
4. **실제 도로망(OpenStreetMap) 즉시 연동**
   * OSM의 실제 도로 링크, 일방통행, 차선 수, 신호등을 파싱하여 실도로에 바로 적용 가능한 어댑터 제공

---

## 📁 프로젝트 구조

```
EZ_LOAD_Algorithm/
├── difficulty_weights.py   # 도로 난이도 지표 정의, 개인화 가중치 빌더, 간선 비용 함수
├── ez_router.py            # Dijkstra / A* 기반 쉬운 길 & 빠른 길 이원화 라우팅 엔진
├── osm_adapter.py          # OpenStreetMap(OSM) 실제 도로망 파서 및 실데이터 라우팅 데모
├── test_ez_router.py       # 핵심 알고리즘 및 개인화 단위 테스트 스위트
├── main.py                 # 원클릭 테스트 및 실데이터 라우팅 데모 실행 진입점
├── data/
│   └── gangnam_roads.osm   # [샘플 데이터] 서울 강남 테헤란로 일대 실제 도로망 (457개 노드, 838개 간선)
├── .gitignore
└── README.md
```

---

## ⚙️ 1. 도로 난이도 비용 함수 (Cost Model)

간선 $e$를 주행할 때의 난이도 점수 $Score(e)$는 다음과 같이 산출됩니다:

$$Score(e) = \text{base\_distance\_km} + \sum_{i} \left( W_i \times C_i \right) + \text{HighwayPenalty}$$

### 🚦 난이도 가중치 지표 ($W_i$)

| 분류 | 요소 코드 | 설명 | 기본 가중치 |
| :--- | :--- | :--- | :--- |
| **회전/교차로** | `u_turn` | 반대 방향 전환 (최고 수준 회피) | **8.0** |
| | `roundabout` | 회전교차로 통과 | **6.0** |
| | `unprotected_left` | 비보호 좌회전 | **4.0** |
| | `sharp_turn` | 도로 자체의 급커브 구간 | **3.0** |
| | `direction_change` | 교차로 좌/우회전 방향 전환 | **1.0** |
| **도로 환경** | `unpaved_road` | 비포장 도로 (km당) | **12.0** |
| | `narrow_road` | 1차로 이하 좁은 이면도로 (km당) | **10.0** |
| | `merge_diverge` | 고속화도로 등 합류/분기 구간 | **4.0** |
| | `lane_change` | 다음 회전을 위한 필수 차로 변경 | **3.0** |
| | `traffic_light` | 신호등 개수 | **1.0** |
| | `traffic_volume` | 상습 혼잡 구간 길이 (km당) | **4.0** |
| **주의 구역** | `accident_zone` | 사고 다발 구간 통과 | **5.0** |
| | `protection_zone` | 어린이/노인 보호구역(스쿨존) | **3.0** |

* **개인화 승수**:
  * 기피 요소(`hard_factors`) 설정 시: 가중치 $\times 2.0$ 상향
  * 선호 요소(`easy_factors`) 설정 시: 가중치 $\times 0.5$ 하향
* **고속도로 선호도 (`highway_preference`)**:
  * $\text{HighwayPenalty} = (\text{highway\_preference} - 0.5) \times 4.0 \times \text{base\_distance\_km}$
  * `0.0` (고속도로 선호) $\rightarrow$ 고속도로 비용 -2.0/km 감산 (고속도로 유도)
  * `1.0` (일반도로 선호) $\rightarrow$ 고속도로 비용 +2.0/km 가산 (일반도로 유도)

---

## 📊 2. 입출력 데이터 규격

### 📥 입력 (Input)
```python
from difficulty_weights import EdgeFeatures, UserContext
from ez_router import EZRouter

# 1. 그래프 (인접 리스트)
graph = {
    "A": [("B", EdgeFeatures(base_distance_km=1.2, traffic_light_count=2, is_narrow_road=False))],
    "B": [...]
}

# 2. 사용자 성향 컨텍스트
context = UserContext(
    highway_preference=0.5,
    hard_factors=["u_turn", "narrow_road"],  # 유턴, 골목길 회피
    easy_factors=["traffic_light"]
)

# 3. 라우터 실행
router = EZRouter(graph, context)
result = router.find_routes("start_node_id", "target_node_id")
```

### 📤 출력 (`DualRouteResult`)
* `easy_route`: 가장 쉬운 길 (`path`, `total_cost`(난이도 점수), `total_distance_km`)
* `fast_route`: 가장 빠른 길 (`path`, `total_cost`(거리), `total_distance_km`)

---

## 🚦 3. 실제 도로망 라우팅 검증 결과

서울 강남역 사거리 ~ 역삼역(테헤란로) 일대 실제 OpenStreetMap 데이터(`gangnam_roads.osm`)를 바탕으로 검증한 결과:

```
[출발지] 강남역 방면 교차로 (노드 10220955574)
[도착지] 역삼역 남측 교차로 (노드 436832396)
```

* **⚡ 가장 빠른 길 (Fast Route)**:
  * 실제 주행 거리: **1.50 km**
  * 주요 경로: 서초대로 $\rightarrow$ 테헤란로 $\rightarrow$ **`테헤란로4길`** $\rightarrow$ **`강남대로84길`** $\rightarrow$ **`논현로85길`**
  * *분석: 거리는 짧으나 초보자가 운전하기 까다로운 좁은 이면도로와 골목길을 직통 관통*
* **🟢 가장 쉬운 길 (Easy Route)**:
  * 실제 주행 거리: **1.65 km** (+150m 우회)
  * 누적 난이도 점수: **41.77** (최저 난이도)
  * 주요 경로: 서초대로 $\rightarrow$ **`테헤란로(대로 유지)`** $\rightarrow$ 테헤란로26길 $\rightarrow$ 논현로85길
  * *분석: 150m를 더 주행하지만 골목길 진입을 최대한 늦추고, 차선이 넓고 주행이 편한 테헤란로 대로 위주로 안내*

---

## 🚀 빠른 시작

### 1. 요구사항
* Python 3.8 이상 (외부 의존성 없이 표준 라이브러리만으로 동작 가능)
* (실제 OSM 실시간 다운로드 사용 시) `requests` 라이브러리 필요

```bash
pip install requests
```

### 2. 실행
```bash
# 단위 테스트 및 강남 도로망 데모 한 번에 실행
python main.py

# 또는 단위 테스트 단독 실행
python test_ez_router.py

# 또는 실제 OSM 데모 단독 실행
python osm_adapter.py
```

---

## 📄 라이선스
이 프로젝트는 [MIT License](LICENSE)를 따릅니다.

