# data/external — 외부 공개 데이터셋 (provenance)

> 여기 데이터 본체는 **git 미추적**(`.gitignore`: `data/external/*` except this README). 이 파일만 커밋되어 **어디서 어떻게 받았는지**를 추적한다. 재현하려면 아래 명령을 그대로 실행.

---

## MIMIC-IV Clinical Database Demo v2.2

- **경로:** `data/external/mimic-iv-clinical-database-demo-2.2/`
- **출처:** PhysioNet — https://physionet.org/content/mimic-iv-demo/2.2/
- **DOI:** https://doi.org/10.13026/dp1f-ex47 (demo) · 상위 MIMIC-IV https://doi.org/10.13026/07hj-2a80
- **버전:** 2.2 (published 2023-01-31)
- **규모:** 환자 100명 (deidentified), `hosp/` 21개 + `icu/` 9개 테이블, gzip CSV, 압축해제 ~16MB
- **라이선스:** **Open Data Commons Open Database License (ODbL) v1.0** — `LICENSE.txt` 참조.
  - ⚠️ ODbL은 **저작자 표기(attribution)** 와 동일 라이선스 공유 의무가 있다. 이 데이터로 만든 결과물·논문엔 MIMIC-IV 인용 필수 (아래).
- **인증(credentialing) 불필요** — full MIMIC-IV(`mimiciv` 정식판)는 CITI 교육+DUA 서명이 필요하지만, 이 **demo는 오픈**이라 계정만 있으면(사실상 계정도 불필요) 즉시 다운로드.
- **무결성:** `SHA256SUMS.txt`로 34개 파일 전부 검증 완료 (수령 2026-07-03, `sha256sum -c` all OK).

### ⚠️ 프로젝트 관점 주의점 (CPX 사례생성용)
> **이 demo는 free-text 임상 노트(clinical notes)를 제외한다.** 구조화 EHR(진단 ICD, 검사 lab, 처방, 차트이벤트, 중환자실 시계열)만 있고 서술형 경과기록/판독문은 없음. CPX 사례의 *서사(narrative)* 가 필요하면:
> - **MIMIC-IV-Note** (deidentified free-text discharge/radiology notes) — 별도 데이터셋이며 **credentialing 필요**(CITI+DUA).
> - 구조화 데이터만으로 온톨로지(원인-증상-질환) 근거·검사수치·처방 패턴을 뽑는 용도로는 이 demo로 충분.

### 재현 (다운로드 → 해제 → 검증)
```bash
cd data/external
# 1) 다운로드 (~16MB, 인증 불필요)
wget -O mimic-iv-clinical-database-demo-2.2.zip \
  https://physionet.org/static/published-projects/mimic-iv-demo/mimic-iv-clinical-database-demo-2.2.zip
# 2) 압축 해제 (unzip 없으면 python)
python3 -c "import zipfile; zipfile.ZipFile('mimic-iv-clinical-database-demo-2.2.zip').extractall('.')"
# 3) 무결성 검증 (전부 OK 나와야 함)
cd mimic-iv-clinical-database-demo-2.2 && sha256sum -c SHA256SUMS.txt
```
대안: `wget -r -N -c -np https://physionet.org/files/mimic-iv-demo/2.2/` (재귀, 중첩 경로 생성) · Google BigQuery `physionet-data.mimiciv_demo` 도 가능.

### 인용 (논문·산출물에 필수)
```
Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R. (2023).
MIMIC-IV Clinical Database Demo (version 2.2). PhysioNet. https://doi.org/10.13026/dp1f-ex47

Goldberger, A., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet.
Circulation [Online]. 101 (23), pp. e215–e220.
```
