# agent-roi-poc

AIエージェント導入による **ROI（処理時間削減率・エラー率）を計測できるダッシュボード付き最小 PoC**。
対象業務は1つの定型業務（**見積書作成**）に限定し、導入前/後を比較できるログ設計にしている。

## 差別化ポイント

「導入後は速くなりました」で終わらせないための2点:

1. **信頼区間つき比較** — 処理時間削減率は**ブートストラップ信頼区間**、エラー率・介入率は
   **Wilson score 信頼区間**で提示。「たまたま速かっただけ」を排除し、
   削減が**統計的に有意か**（CI が 0 をまたがないか）を判定する。
2. **人間介入率トラッキング** — AI 導入後に「人間の確認/修正が必要だった割合」を全実行で記録。
   介入コストを無視した見かけ上の ROI を防ぎ、**実効 ROI** を評価できる。

すべて **API キー不要**（決定的シミュレーション）で動作。実測ログがあれば
`MetricsTracker.load_jsonl` で差し替えるだけ。

## ログ設計（導入前/後の比較）

1レコード = 1タスク実行。`mode`(before/after) で導入前後を分離:

```json
{"mode":"after","task":"見積書作成","duration_sec":178.3,"had_error":false,"human_intervention":true,"ts":"..."}
```

## クイックスタート

```bash
python demo.py                      # ログ生成 -> ROIレポート(CLI)
python dashboard/app.py             # Streamlitあれば GUI、無ければ CLIレポート
python -m pytest -q                 # テスト(外部依存なし)
# GUI: pip install streamlit && streamlit run dashboard/app.py
```

## 構成

```
src/
  agent.py            # 対象業務(見積書作成)の導入前/後シミュレーション
  metrics/
    tracker.py        # ログ設計(TaskRun) + jsonl 保存/読込
    stats.py          # 削減率ブートストラップCI / 比率Wilson CI / 比較
data/before, data/after   # 導入前/後ログ(jsonl)
dashboard/app.py      # ROIダッシュボード(Streamlit / CLIフォールバック)
tests/                # CIの性質・介入率・ログ往復を検証
```
