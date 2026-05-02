# Book Order Guard API

Book Order Guard API는 온라인 도서 주문 요청을 룰 기반으로 검증하고, 주문 가능(APPROVED), 주문 불가(REJECTED), 확인 필요(REVIEW) 상태와 가격 계산 결과를 반환하는 FastAPI 기반 웹/API 서비스입니다.

이 프로젝트는 도서 주문 검증 기능을 구현하면서 GitHub, pytest, GitHub Actions, Docker, Render를 연결해 하나의 DevOps 파이프라인을 구성하는 것을 목표로 했습니다.

---

## 1. 프로젝트 개요

- 프로젝트명: Book Order Guard API
- 프로젝트 주제: 룰 기반 도서 주문 검증 서비스
- 개발 방식: FastAPI + 정적 HTML UI + pytest + GitHub Actions + Docker + Render
- GitHub 저장소: https://github.com/flosure23/book-order-guard-api
- 배포 주소: https://book-order-guard-api.onrender.com/

---

## 2. 주요 기능

### 2.1 도서 주문 검증

사용자가 입력한 도서 주문 정보를 기반으로 주문 가능 여부를 판단합니다.

검증 대상은 다음과 같습니다.

- 도서 ID
- 도서명
- 단가
- 주문 수량
- 재고
- 회원 등급
- 쿠폰 코드
- 배송 지역

### 2.2 주문 상태 반환

주문 검증 결과는 세 가지 상태로 반환됩니다.

| 상태 | 의미 |
|---|---|
| `APPROVED` | 주문 가능 |
| `REJECTED` | 주문 불가 |
| `REVIEW` | 확인 필요 |

### 2.3 가격 계산

주문 정보에 따라 다음 가격 정보를 계산합니다.

- 원가
- 회원 등급 할인
- 쿠폰 할인
- 배송비
- 최종 결제 금액

### 2.4 간단한 HTML UI

별도의 프론트엔드 프레임워크는 사용하지 않았습니다.  
FastAPI에서 정적 HTML 파일을 반환하고, JavaScript `fetch()`를 사용하여 주문 검증 API를 호출합니다.

사용자는 브라우저에서 도서 주문 정보를 입력한 뒤 주문 검증 결과를 확인할 수 있습니다.

---

## 3. 주문 검증 룰

### 3.1 입력값 검증

다음 조건을 만족하지 않으면 API 요청 단계에서 오류가 발생합니다.

- `book_id`: 1글자 이상
- `title`: 1글자 이상
- `unit_price`: 1 이상
- `quantity`: 1 이상
- `stock`: 0 이상
- `member_grade`: `BASIC`, `SILVER`, `GOLD`, `VIP` 중 하나
- `region`: `NORMAL`, `REMOTE_ISLAND`, `MILITARY_PO_BOX`, `OVERSEAS` 중 하나

### 3.2 회원 등급 할인

| 회원 등급 | 할인율 |
|---|---:|
| `BASIC` | 0% |
| `SILVER` | 5% |
| `GOLD` | 10% |
| `VIP` | 15% |

### 3.3 쿠폰 할인

| 쿠폰 코드 | 할인 |
|---|---:|
| `WELCOME10` | 회원 할인 적용 후 금액에서 추가 10% 할인 |

쿠폰이 없으면 `null` 또는 빈 값으로 처리합니다.  
지원하지 않는 쿠폰 코드가 입력되면 주문 불가 상태로 처리합니다.

### 3.4 무료배송 기준

할인 적용 후 상품 금액이 30,000원 이상이면 배송비는 0원입니다.  
30,000원 미만이면 배송비 3,000원을 부과합니다.

### 3.5 배송 지역 처리

| 배송 지역 | 처리 결과 |
|---|---|
| `NORMAL` | 일반 배송 가능 |
| `REMOTE_ISLAND` | 확인 필요 |
| `MILITARY_PO_BOX` | 확인 필요 |
| `OVERSEAS` | 주문 불가 |

### 3.6 재고 처리

| 조건 | 처리 결과 |
|---|---|
| 주문 수량이 재고보다 많음 | `REJECTED` |
| 주문 후 잔여 재고가 1권 이하 | `REVIEW` |
| 그 외 | `APPROVED` |

---

## 4. API 목록

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/` | HTML UI 화면 |
| `GET` | `/health` | 서버 상태 확인 |
| `POST` | `/orders/validate` | 도서 주문 검증 및 가격 계산 |
| `GET` | `/rules` | 적용 중인 검증 룰 목록 조회 |
| `GET` | `/logs-test` | 운영 로그 출력 확인 |

---

## 5. API 요청 예시

### 5.1 주문 검증 요청

```json
{
  "book_id": "B001",
  "title": "Database Systems",
  "unit_price": 25000,
  "quantity": 2,
  "stock": 5,
  "member_grade": "GOLD",
  "coupon_code": "WELCOME10",
  "region": "NORMAL"
}
```

### 5.2 주문 검증 응답 예시

```json
{
  "status": "APPROVED",
  "message": "주문이 승인되었습니다.",
  "price": {
    "original_price": 50000,
    "member_discount": 5000,
    "coupon_discount": 4500,
    "shipping_fee": 0,
    "final_price": 40500
  },
  "reasons": []
}
```

---

## 6. 실행 방법

### 6.1 가상환경 생성

```powershell
python -m venv .venv
```

### 6.2 가상환경 실행

```powershell
.\.venv\Scripts\activate
```

### 6.3 의존성 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6.4 로컬 서버 실행

```powershell
uvicorn app.main:app --reload
```

### 6.5 실행 확인

브라우저에서 아래 주소에 접속합니다.

```text
http://127.0.0.1:8000/
```

서버 상태 확인은 아래 주소에서 가능합니다.

```text
http://127.0.0.1:8000/health
```

API 문서는 아래 주소에서 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

---

## 7. 테스트 실행 방법

본 프로젝트는 pytest를 사용하여 주문 검증 API의 주요 룰을 자동 테스트합니다.

```powershell
pytest
```

테스트 항목은 다음 내용을 포함합니다.

* `/health` 정상 응답
* 정상 주문 승인
* 재고 부족 주문 거절
* 수량 0 입력 검증
* 가격 0 입력 검증
* GOLD 회원 할인 계산
* WELCOME10 쿠폰 할인 계산
* 무료배송 경계값 확인
* 도서산간 지역 REVIEW 처리
* 잔여 재고 1권 이하 REVIEW 처리
* 해외 배송 REJECTED 처리

---

## 8. GitHub Actions CI

GitHub Actions를 사용하여 CI를 구성했습니다.

CI는 다음 상황에서 자동으로 실행됩니다.

* `main` 브랜치에 push
* `main` 브랜치로 Pull Request 생성

CI 수행 작업은 다음과 같습니다.

1. GitHub 저장소 코드 체크아웃
2. Python 환경 설정
3. `requirements.txt` 기반 의존성 설치
4. pytest 실행

이를 통해 코드 변경 후 기존 주문 검증 기능이 정상 동작하는지 자동으로 확인할 수 있습니다.

---

## 9. Docker 실행 방법

### 9.1 Docker 이미지 빌드

```powershell
docker build -t book-order-guard-api .
```

### 9.2 Docker 컨테이너 실행

```powershell
docker run -d --name book_order_guard -e PORT=10000 -p 10000:10000 book-order-guard-api
```

### 9.3 Docker 실행 확인

```text
http://127.0.0.1:10000/health
```

### 9.4 컨테이너 종료 및 삭제

```powershell
docker rm -f book_order_guard
```

---

## 10. Render 배포

본 프로젝트는 Render를 사용하여 배포했습니다.

배포 방식은 다음과 같습니다.

1. GitHub 저장소와 Render 연결
2. Web Service 생성
3. Docker 기반 배포 설정
4. `main` 브랜치 기준 배포
5. 배포 URL에서 서비스 실행 확인

배포 후 다음 주소에서 실행을 확인할 수 있습니다.

```text
https://book-order-guard-api.onrender.com/
https://book-order-guard-api.onrender.com/health
https://book-order-guard-api.onrender.com/docs
```

---

## 11. 운영 로그 확인

FastAPI 애플리케이션에 Python logging을 적용하여 주요 요청과 처리 결과를 로그로 확인할 수 있도록 구성했습니다.

로그가 남는 주요 상황은 다음과 같습니다.

* `/health` 요청
* `/orders/validate` 주문 검증 요청
* 주문 검증 결과
* `/logs-test` 로그 테스트 요청

Render 배포 후에는 Render 대시보드의 Logs 메뉴에서 운영 로그를 확인할 수 있습니다.

예시 로그는 다음과 같습니다.

```text
INFO:book-order-guard:health check requested
INFO:book-order-guard:order validation requested book_id=B001 quantity=2 grade=GOLD region=NORMAL
INFO:book-order-guard:order validation result status=APPROVED final_price=40500 reasons=[]
WARNING:book-order-guard:this is a warning log for operation check
```

---

## 12. 장애 시나리오 및 해결 기록

본 프로젝트에서는 DevOps 파이프라인에서 테스트와 CI가 어떤 역할을 하는지 확인하기 위해 장애 시나리오를 의도적으로 재현하고 해결했습니다.

### 12.1 무료배송 경계값 버그

* 문제: 30,000원 이상 무료배송이어야 하지만 조건식을 `> 30000`으로 작성하여 30,000원 주문에 배송비가 부과됨
* 발견: pytest와 GitHub Actions에서 무료배송 경계값 테스트 실패
* 해결: 조건식을 `>= 30000`으로 수정
* 결과: 수정 후 테스트와 CI 통과

### 12.2 GOLD 회원 할인율 회귀 버그

* 문제: GOLD 회원 할인율이 10%여야 하지만 5%로 잘못 변경됨
* 발견: GOLD 회원 할인 계산 테스트 실패
* 해결: GOLD 할인율을 다시 10%로 수정
* 결과: 수정 후 테스트와 CI 통과

### 12.3 requirements.txt 의존성 누락

* 문제: 테스트 실행에 필요한 `httpx` 의존성이 `requirements.txt`에서 누락됨
* 발견: GitHub Actions의 깨끗한 실행 환경에서 테스트 실패
* 해결: `requirements.txt`에 `httpx`를 다시 추가
* 결과: 수정 후 GitHub Actions CI 통과

### 12.4 Render/컨테이너 포트 바인딩 문제

* 문제: uvicorn 실행 시 host와 port 설정이 컨테이너 및 Render 환경과 맞지 않으면 외부 접속 실패
* 발견: 컨테이너 실행 후 외부 포트에서 `/health` 접속 실패
* 해결: `--host 0.0.0.0`과 `${PORT}` 환경변수를 사용하도록 Dockerfile 수정
* 결과: Docker 컨테이너와 Render 배포 환경에서 정상 접속 확인

---

## 13. 개발 흐름

본 프로젝트는 Git 기반 개발 흐름을 따랐습니다.

주요 개발 흐름은 다음과 같습니다.

```text
로컬 코드 수정
→ feature 또는 bugfix 브랜치 생성
→ 커밋
→ GitHub push
→ Pull Request 생성
→ GitHub Actions CI 실행
→ 테스트 통과 확인
→ main 브랜치 merge
→ Docker 및 Render 배포 확인
→ 운영 로그 확인
```

---

## 14. 커밋 메시지 규칙

커밋 메시지는 변경 목적이 드러나도록 다음 규칙을 사용했습니다.

| Prefix     | 의미                       |
| ---------- | ------------------------ |
| `feat`     | 기능 추가                    |
| `fix`      | 버그 수정                    |
| `test`     | 테스트 추가 또는 수정             |
| `ci`       | GitHub Actions 등 CI 설정   |
| `chore`    | 환경 설정, 패키지 관리, Docker 설정 |
| `docs`     | README 및 문서 수정           |
| `refactor` | 기능 변화 없는 코드 구조 개선        |
| `bug`      | 장애 시나리오 재현용 커밋           |

예시:

```text
feat: add basic FastAPI app and health endpoint
feat: implement order validation rules
feat: add simple order validation UI
test: add order validation test cases
ci: add GitHub Actions pytest workflow
chore: add Dockerfile for container execution
fix: correct free shipping boundary condition
fix: configure uvicorn host and port for container deployment
docs: finalize project documentation
```

---

## 15. 프로젝트 구조

```text
book-order-guard-api/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ schemas.py
│  ├─ pricing.py
│  ├─ rules.py
│  └─ logging_config.py
│
├─ static/
│  └─ index.html
│
├─ tests/
│  ├─ conftest.py
│  └─ test_api.py
│
├─ .github/
│  └─ workflows/
│     └─ ci.yml
│
├─ Dockerfile
├─ requirements.txt
├─ README.md
├─ .gitignore
└─ .dockerignore
```

---

## 16. 사용 기술

| 구분              | 기술               |
| --------------- | ---------------- |
| Language        | Python           |
| Web Framework   | FastAPI          |
| UI              | HTML, JavaScript |
| Test            | pytest           |
| CI              | GitHub Actions   |
| Container       | Docker           |
| Deploy          | Render           |
| Version Control | Git, GitHub      |