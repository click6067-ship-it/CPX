# Langfuse 셀프호스트 (무료·오픈소스·데이터 egress 0)

이 프로젝트의 거버넌스(사례·저작권 RAG가 제3자로 안 나감)에 최적. 데이터가 **이 머신 안에만** 머문다.
단 Langfuse v3 스택은 무거우니(ClickHouse 등) RAM 확보가 필요하다.

## 제약 (이 머신 기준)
- WSL passwordless sudo 미설정 → **docker 설치는 사용자가 sudo로 직접** 실행.
- RAM 5.8GB → v3 풀스택은 빡빡. 가능하면 WSL RAM ↑(아래) + 불필요 프로세스 종료.

## 1) docker 설치  ← 사용자가 실행 (sudo 비번 필요)
프롬프트에 `!` 붙여 세션에서 실행하거나, WSL 터미널에서:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER          # sudo 없이 docker 쓰기(그룹 적용엔 재시작 필요)
sudo service docker start              # systemd면 자동, 아니면 수동 기동
```
> 그룹 적용을 위해 Windows PowerShell 에서 `wsl --shutdown` 후 터미널 재오픈 권장
> (단 이 경우 현재 세션·백그라운드 서버가 종료됨). 또는 docker 명령을 `sudo` 로 실행.

## 2) (권장) WSL RAM 늘리기  ← 윈도우 PC RAM 충분할 때
Windows 사용자 폴더 `C:\Users\<나>\.wslconfig` 에:
```ini
[wsl2]
memory=10GB
```
저장 후 PowerShell `wsl --shutdown` → 재오픈. (PC 총 RAM ≥16GB 권장. ~8GB면 v3 셀프호스트 비권장.)

## 3) Langfuse 기동 (공식 compose)  ← docker 준비되면 Claude 가 실행/대행 가능
```bash
git clone https://github.com/langfuse/langfuse        # 별도 폴더(이 레포 밖)에
cd langfuse
docker compose up -d                                   # web=3000, db/clickhouse/redis/minio 자동
```
> 포트 3000 은 다른 서비스와 충돌 가능 → 필요시 compose 의 langfuse-web 포트 변경.

## 4) 프로젝트·키 생성  ← 사용자(브라우저)
1. http://localhost:3000 접속 → 계정 생성(로컬).
2. New Project → Settings → **API Keys** → `pk-lf-…` / `sk-lf-…` 복사.

## 5) CPX .env 연동 + 라이브 demo  ← Claude 가 대행
```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
CPX_TRACE_ACK=1
```
→ `CPX_TRACE_ACK=1 PYTHONPATH=src .venv/bin/python scripts/sample_trace.py`
   (셀프호스트라 redaction 안 해도 egress 0지만, 기본 마스킹은 그대로 유지 — 공개 캡처용으로도 안전.)
