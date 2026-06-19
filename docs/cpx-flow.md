# CPX-AI 작동방식 (다이어그램)

> GitHub·노션에서 아래 블록이 자동 렌더됩니다. 편집 그림은 `cpx-flow.excalidraw`(excalidraw.com), 원본 mermaid는 `cpx-flow.mmd`.
> 모델·데이터 상세 = [`transparency.md`](transparency.md) · 검증 설계 = [`validation-design.md`](validation-design.md)

```mermaid
flowchart TD
  subgraph A["A. 사례개발 루프 (교수 지원)"]
    seed["기존 CPX 사례(씨앗)"] --> gen["① 생성<br/>gpt-5.5"] --> review["② 검토<br/>gpt-5.5 · 구조+임상"] --> accept{"Accept?"}
    rag["RAG 근거<br/>dense: Gemini 임베딩<br/>sparse: BM25 → 교과서(MedQA)"] --> review
    accept -- 예 --> confirmed["확정 사례"]
    accept -- "아니오 (수정 루프)" --> gen
  end
  subgraph B["B. 검증 H2 (현재 파일럿)"]
    prof["교수 과거 피드백<br/>(정답지)"] --> blind["블라인드 설문<br/>교수 A/B 익명 평가<br/>cpx-adj-web"]
    ai["② AI 리뷰"] --> blind --> agg["집계<br/>recall·precision·ICC·blind성공·CI"]
  end
  subgraph C["C. 학생 런타임"]
    confirmed --> vp["③ 가상환자<br/>GPT-4o · 음성"] --> stu["학생 대화"] --> grade["④ 자동채점<br/>GPT-4o"] --> fb["피드백"]
  end
  review --> ai
```

**핵심:** Claude(계획서)→결제 보류로 ①② = **gpt-5.5**, ③④ = GPT-4o, RAG 임베딩 = Gemini. 어댑터(`llm.py`)라 결제 풀리면 Claude로 1줄 교체.
