# Book Order Guard ML

도서 주문을 기존 규칙으로 검증하고, 머신러닝 모델로 추가 검토 위험도를 예측하는 FastAPI 기반 MLOps 프로젝트입니다.

- GitHub: https://github.com/flosure23/book-order-guard-api
- 배포 서비스: https://book-order-guard-api.onrender.com/
- Swagger API 문서: https://book-order-guard-api.onrender.com/docs

## 1. 프로젝트 개요

기존 Book Order Guard 서비스는 주문 수량, 재고, 회원 등급, 쿠폰과 배송 지역을 규칙으로 검사하여 `APPROVED`, `REVIEW`, `REJECTED` 상태와 결제 금액을 반환합니다.

이 프로젝트에서는 기존 기능을 유지하면서 다음 MLOps 기능을 추가했습니다.

- 고객·주문 정보를 이용한 ML 검토 위험도 예측
- LogisticRegression과 RandomForestClassifier 비교
- MLflow 기반 실험, 지표, 모델 파일과 모델 버전 관리
- Model Registry의 `champion` alias를 이용한 운영 모델 선택
- MLflow 연결 실패 시 로컬 모델 fallback
- 예측 로그와 운영자 피드백 저장
- 피드백을 기본 학습 데이터와 병합한 재학습
- GitHub Actions 자동 테스트 및 모델 학습
- Docker 컨테이너 검증과 Render 배포
- 이전 모델 버전으로의 롤백

## 2. 주요 기능

### 2.1 룰 기반 주문 검증

`POST /orders/validate`는 다음 내용을 확인합니다.

- 주문 수량이 재고보다 많으면 `REJECTED`
- 해외 배송은 `REJECTED`
- 지원하지 않는 쿠폰은 `REJECTED`
- 주문 후 잔여 재고가 1권 이하이면 `REVIEW`
- 도서산간 또는 군부대 사서함 배송은 `REVIEW`
- 그 외 주문은 `APPROVED`

회원 등급 할인, `WELCOME10` 쿠폰 할인과 배송비를 적용해 최종 결제 금액도 계산합니다.

### 2.2 ML 포함 주문 검증

`POST /orders/validate-with-ml`은 룰 검증 결과와 ML 위험도 예측을 함께 반환합니다.

| 위험 점수 | 위험 등급 | ML 추천 |
|---:|---|---|
| 0.00 이상 0.40 미만 | `LOW` | `APPROVED` |
| 0.40 이상 0.50 미만 | `MEDIUM` | `APPROVED` |
| 0.50 이상 | `HIGH` | `REVIEW` |

최종 주문 상태는 다음 우선순위로 결정합니다.

1. 룰 결과가 `REJECTED`이면 최종 결과도 `REJECTED`
2. 룰 결과가 `REVIEW`이면 최종 결과도 `REVIEW`
3. 룰 결과가 `APPROVED`이고 ML 위험 등급이 `HIGH`이면 `REVIEW`
4. 나머지는 `APPROVED`

### 2.3 모델 상태와 운영자 피드백

- `/model/health`: 모델 사용 가능 여부 확인
- `/model/info`: 현재 사용 중인 모델 URI, 모델 종류, f1-score와 run ID 확인
- `/feedback`: 운영자가 실제 결과를 `APPROVED` 또는 `REVIEW`로 저장
- `logs/predictions.csv`: ML 예측 요청과 결과 기록
- `logs/feedback.csv`: 재학습에 사용할 운영자 피드백 기록

## 3. 전체 동작 흐름

```text
주문 입력
  ├─ 룰 기반 검증 및 가격 계산
  └─ ML 모델 위험도 예측
          ↓
룰 결과와 ML 결과 결합
          ↓
최종 주문 상태 반환
          ↓
예측 로그 및 운영자 피드백 저장
          ↓
기본 데이터와 피드백 병합
          ↓
재학습 및 MLflow 신규 모델 버전 등록
          ↓
검토 후 champion alias 수동 지정
```

개발·배포 흐름은 다음과 같습니다.

```text
Git 브랜치 및 Pull Request
→ GitHub Actions 테스트
→ main 병합 후 모델 자동 학습
→ MLflow run 및 모델 버전 등록
→ champion 수동 선택
→ Docker 검증
→ Render 배포 및 운영 로그 확인
```

## 4. 기술 구성

| 구분 | 기술 |
|---|---|
| Language | Python 3.11 |
| API | FastAPI, Uvicorn, Pydantic |
| UI | HTML, CSS, JavaScript |
| Data | pandas |
| ML | scikit-learn, joblib |
| Experiment / Registry | MLflow |
| Test | pytest, httpx |
| CI/CD | GitHub Actions |
| Container | Docker |
| Deploy | Render |

## 5. 프로젝트 구조

```text
book-order-guard-api/
├─ app/
│  ├─ main.py                 # FastAPI endpoint
│  ├─ rules.py                # 룰 기반 주문 검증
│  ├─ pricing.py              # 할인 및 가격 계산
│  ├─ schemas.py              # 기본 주문 요청·응답
│  ├─ ml_schemas.py           # ML 요청·응답 및 피드백 schema
│  ├─ order_ml.py             # ML 예측과 최종 상태 결정
│  ├─ model_loader.py         # MLflow champion 및 fallback 로딩
│  ├─ prediction_logger.py    # 예측 로그 저장
│  ├─ feedback.py             # 운영자 피드백 저장
│  └─ config.py               # 모델 및 MLflow 환경 설정
├─ ml/
│  ├─ train.py                # 모델 학습·평가·MLflow 등록
│  ├─ build_retraining_data.py# 피드백 기반 재학습 데이터 생성
│  ├─ data/                   # 기본 학습·테스트 데이터
│  └─ artifacts/              # 로컬 모델 및 평가 결과
├─ static/
│  └─ index.html              # 룰·ML 검증 및 피드백 UI
├─ tests/
│  ├─ test_api.py
│  ├─ test_ml_api.py
│  └─ test_retraining_data.py
├─ .github/workflows/
│  ├─ ci.yml
│  └─ train.yml
├─ Dockerfile
└─ requirements.txt
```

## 6. 로컬 실행

### 6.1 요구 환경

- Python 3.11
- Git
- 선택 사항: Docker, MLflow Tracking Server

### 6.2 가상환경과 의존성 설치

PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6.3 로컬 모델로 실행

MLflow 서버 없이 저장소에 포함된 로컬 모델로 실행하는 가장 간단한 방법입니다.

```powershell
$env:MODEL_MODE="local"
uvicorn app.main:app --reload
```

실행 후 다음 주소를 확인합니다.

- UI: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs
- 서비스 상태: http://127.0.0.1:8000/health
- 모델 정보: http://127.0.0.1:8000/model/info

## 7. 환경 변수

| 환경 변수 | 기본값 | 설명 |
|---|---|---|
| `MODEL_MODE` | `mlflow` | `mlflow` 또는 `local` 모델 로딩 방식 |
| `MLFLOW_TRACKING_URI` | `sqlite:///mlflow.db` | MLflow Tracking Server 주소 |
| `MODEL_URI` | `models:/book-order-review-model@champion` | 운영 모델 URI |
| `LOCAL_MODEL_PATH` | `ml/artifacts/review_risk_model.joblib` | fallback 모델 파일 |
| `TRAIN_DATA_PATH` | `ml/data/orders_train.csv` | 학습 데이터 경로 |
| `MODEL_ARTIFACT_DIR` | `ml/artifacts` | 학습 결과 저장 경로 |
| `PORT` | `10000` | Docker 및 배포 서버 포트 |

`MODEL_MODE=mlflow`에서 MLflow 모델 로딩에 실패하면 로컬 joblib 모델을 fallback으로 사용합니다. `/model/health`가 정상이어도 fallback 모델일 수 있으므로 실제 운영 모델은 `/model/info`에서 확인합니다.

## 8. API

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/` | 웹 UI |
| `GET` | `/health` | 서비스 상태 |
| `GET` | `/rules` | 룰 및 ML 위험도 기준 |
| `POST` | `/orders/validate` | 룰 기반 주문 검증과 가격 계산 |
| `POST` | `/orders/validate-with-ml` | 룰 검증과 ML 위험도 예측 |
| `GET` | `/model/health` | 모델 로딩 상태 |
| `GET` | `/model/info` | 현재 모델의 상세 정보 |
| `POST` | `/feedback` | 운영자 정답 피드백 저장 |
| `GET` | `/logs-test` | 운영 로그 출력 확인 |

### 8.1 ML 포함 검증 요청 예시

```json
{
  "book_id": "B-ML-001",
  "title": "MLOps Practice Book",
  "unit_price": 90000,
  "quantity": 2,
  "stock": 20,
  "member_grade": "BASIC",
  "coupon_code": "WELCOME10",
  "region": "NORMAL",
  "customer_age_days": 6,
  "previous_order_count": 0,
  "recent_order_count_7d": 4,
  "coupon_usage_count_30d": 5,
  "is_preorder": false,
  "address_risk_level": "HIGH"
}
```

### 8.2 응답 예시

```json
{
  "rule_status": "APPROVED",
  "review_risk_score": 0.9167,
  "review_risk_level": "HIGH",
  "ml_recommendation": "REVIEW",
  "final_status": "REVIEW",
  "risk_reasons": [
    "신규 고객의 고액 주문입니다.",
    "최근 7일 주문 횟수가 많습니다.",
    "최근 30일 쿠폰 사용 횟수가 많습니다.",
    "배송지 위험도가 높습니다."
  ],
  "model_info": {
    "model_name": "book-order-review-model",
    "model_uri": "models:/book-order-review-model@champion",
    "model_type": "RandomForestClassifier",
    "f1_score": 1.0,
    "run_id": "1d7c17a940f74c489916f9ed20a8ec4b",
    "loaded": true
  }
}
```

## 9. 모델 학습

### 9.1 데이터와 모델

- 기본 학습 데이터: `ml/data/orders_train.csv`
- 테스트 데이터: `ml/data/orders_test.csv`
- 정답 항목: `manual_review_needed`
- 후보 모델:
  - LogisticRegression
  - RandomForestClassifier
- 평가 지표: f1-score

수치형 입력에는 `StandardScaler`, 범주형 입력에는 `OneHotEncoder`를 적용하고, 전처리와 분류기를 하나의 scikit-learn Pipeline으로 저장합니다.

### 9.2 MLflow 서버 실행

```powershell
mlflow server `
  --host 0.0.0.0 `
  --port 6430 `
  --backend-store-uri sqlite:///mlflow.db `
  --artifacts-destination ./mlartifacts
```

다른 PowerShell에서 Tracking URI를 설정하고 학습합니다.

```powershell
$env:MLFLOW_TRACKING_URI="http://127.0.0.1:6430"
python -m ml.train
```

학습 코드는 각 후보 모델에 대해 다음 항목을 MLflow에 기록합니다.

- parameter: 모델 종류, 데이터 파일, 행 수, 입력 변수 수
- metric: f1-score
- artifact: 분류 성능 보고서, joblib 모델 파일
- model: MLflow sklearn model
- registry: `book-order-review-model`의 신규 version

가장 높은 f1-score 모델은 `ml/artifacts/review_risk_model.joblib`에도 저장하며, 저장한 모델을 다시 불러와 예측 확률을 검사합니다.

소규모 합성 데이터 기준 초기 실험 결과는 다음과 같습니다.

| 모델 | f1-score |
|---|---:|
| LogisticRegression | 약 0.6667 |
| RandomForestClassifier | 1.0000 |

이 결과는 프로젝트의 제한된 합성 테스트 데이터에서 나온 모델 비교 결과이며 일반적인 운영 성능을 의미하지 않습니다.

## 10. MLflow 모델 등록과 서비스 반영

학습 시 모델 버전은 자동으로 등록하지만, 운영 모델을 가리키는 `champion` alias는 자동으로 변경하지 않습니다.

```text
학습 완료
→ MLflow run과 f1-score 확인
→ 등록된 model version 확인
→ 운영할 version에 champion alias 수동 지정
→ API 서버 재시작
→ /model/info에서 적용 결과 확인
```

서비스는 다음 URI로 champion 모델을 불러옵니다.

```text
models:/book-order-review-model@champion
```

이전 모델로 롤백할 때는 Model Registry에서 이전 version으로 `champion` alias를 이동한 뒤 서비스를 재시작합니다. 모델 파일을 직접 교체하지 않고 운영 버전을 변경할 수 있습니다.

## 11. 운영자 피드백과 재학습

웹 UI에서 ML 검증 후 실제 결과에 맞는 피드백 버튼을 누르면 `logs/feedback.csv`에 주문 정보와 정답이 저장됩니다.

재학습 데이터는 다음 명령으로 생성합니다.

```powershell
python -m ml.build_retraining_data
```

이 명령은 기본 학습 데이터와 피드백을 합치고 중복 주문 조건을 제거하여 `ml/data/orders_retrain.csv`를 생성합니다.

생성한 데이터로 재학습합니다.

```powershell
$env:TRAIN_DATA_PATH="ml/data/orders_retrain.csv"
$env:MODEL_ARTIFACT_DIR="logs/retraining_artifacts"
$env:MLFLOW_TRACKING_URI="http://127.0.0.1:6430"

python -m ml.train
```

재학습 후에도 신규 version만 등록되며, 성능과 실행 결과를 확인한 뒤 `champion`을 수동으로 변경합니다.

## 12. 테스트

```powershell
python -m pytest
```

현재 테스트는 총 22개이며 다음 범위를 포함합니다.

- 룰 기반 주문 검증과 가격 계산
- 회원 할인, 쿠폰, 무료배송 경계값
- 재고 부족과 배송 지역 처리
- ML 위험도 구간과 최종 상태 결정
- 모델 상태 및 정보 API
- 잘못된 ML 입력 검증
- 운영자 피드백 API
- 피드백 데이터와 기본 데이터의 병합

## 13. GitHub Actions

### 13.1 Python CI

`.github/workflows/ci.yml`

- `main` push 또는 main 대상 Pull Request에서 실행
- Python 3.11 환경 구성
- 의존성 설치
- 전체 pytest 실행

### 13.2 Train ML Model

`.github/workflows/train.yml`

- Pull Request에서는 test job만 실행
- main push 또는 수동 실행 시 test 통과 후 train job 실행
- 원격 MLflow에 run과 model version 등록
- 학습된 로컬 모델 파일을 GitHub Actions artifact로 업로드

원격 학습에는 Repository Secret이 필요합니다.

```text
MLFLOW_TRACKING_URI = 외부에서 접근 가능한 MLflow Tracking Server 주소
```

## 14. Docker

### 14.1 이미지 빌드

```powershell
docker build -t book-order-guard-ml .
```

### 14.2 로컬 모델로 실행

```powershell
docker run -d `
  --name book_order_guard_ml `
  -e PORT=10000 `
  -e MODEL_MODE="local" `
  -p 10000:10000 `
  book-order-guard-ml
```

### 14.3 MLflow champion 모델로 실행

```powershell
docker run -d `
  --name book_order_guard_ml `
  -e PORT=10000 `
  -e MODEL_MODE="mlflow" `
  -e MODEL_URI="models:/book-order-review-model@champion" `
  -e MLFLOW_TRACKING_URI="https://YOUR-MLFLOW-SERVER" `
  -p 10000:10000 `
  book-order-guard-ml
```

실행 확인:

```powershell
Invoke-RestMethod http://127.0.0.1:10000/health
Invoke-RestMethod http://127.0.0.1:10000/model/info
```

종료 및 삭제:

```powershell
docker rm -f book_order_guard_ml
```

## 15. Render 배포

Render Docker Web Service에 저장소를 연결하고 다음 환경 변수를 설정합니다.

| Key | Value |
|---|---|
| `PORT` | `10000` |
| `MODEL_MODE` | `mlflow` |
| `MODEL_URI` | `models:/book-order-review-model@champion` |
| `MLFLOW_TRACKING_URI` | 외부 MLflow Tracking Server 주소 |

배포 후 `/health`, `/model/health`, `/model/info`, `/orders/validate-with-ml`과 Render Logs를 함께 확인합니다.

현재 배포 주소:

```text
https://book-order-guard-api.onrender.com/
```

## 16. 운영 로그와 장애 대응

애플리케이션은 다음 내용을 로그로 기록합니다.

- 룰 기반 주문 검증 요청과 결과
- ML 포함 검증 요청
- MLflow 모델 로딩
- 위험 점수, 위험 등급과 최종 상태
- 모델 fallback 발생
- 운영자 피드백 저장

프로젝트에서 확인한 주요 장애 사례는 다음과 같습니다.

| 문제 | 원인 | 해결 |
|---|---|---|
| GitHub Actions artifact 업로드 실패 | Windows 절대 경로가 Linux runner에서 `/C:`로 해석됨 | 공유 MLflow experiment를 `mlflow-artifacts:/` 경로로 재생성 |
| CI에서 MLflow import 실패 | `requirements.txt`에서 MLflow 의존성 누락 | 의존성 복구 후 Actions 재실행 |
| `/model/health`는 정상이나 운영 모델이 다름 | 잘못된 `MODEL_URI`로 MLflow 로드 실패 후 fallback 사용 | `/model/info`로 실제 모델 확인 후 URI 복구 |
| ML 예측 중 입력 열 오류 | 학습과 서비스의 입력 항목 이름 불일치 | 입력 열 이름을 학습 Pipeline과 동일하게 복구 |

## 17. 제한 사항과 개선 방향

- 현재 학습 데이터는 프로젝트 검증을 위한 소규모 합성 데이터입니다.
- MLflow 서버와 모델 파일은 영구 서버 및 외부 object storage로 이전할 수 있습니다.
- Render의 로컬 CSV 로그는 재배포 시 유지되지 않을 수 있으므로 운영 환경에서는 데이터베이스 저장이 필요합니다.
- 실제 운영에서는 더 많은 데이터, 독립 검증 데이터, 교차 검증과 데이터 변화 감시가 필요합니다.

---

학번: 190336<br>
이름: 김준영
