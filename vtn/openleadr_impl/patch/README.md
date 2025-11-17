# patch ディレクトリについて

このディレクトリは、openleadr の仕様不足を**アプリケーション側で吸収するためのパッチコード**を置く場所です。
パッチを適応する場合は`MyOpenADRServer`より前にインポートを行ってください。

---

## ファイル一覧

### `patch_openleadr_timedelta.py`

`openleadr` ライブラリの `utils.timedeltaformat` が、  
**ゼロ期間 (`timedelta(0)`) を RFC5545 / OpenADR 的に正しい `"PT0S"` として出力しない問題**を回避するパッチです。

#### 背景

- `openleadr.utils.timedeltaformat` は、`datetime.timedelta` を RFC5545 形式の duration 文字列へ変換します。
- しかし、`timedelta(0)` を渡した場合に `"PT0S"` ではなく `"P"` のような不正な文字列を返してしまいます。
- OpenADR のメッセージでは `PT0S` のようなゼロ秒の期間が出現し得るため、
  `"P"` が出力されると XML として不正となり、相手側でパースエラーや誤動作の原因になります。

#### パッチ内容

`patch_openleadr_timedelta.py` では、次の 2 点を行っています。

1. `utils.timedeltaformat` をラップし、
   - 入力が `timedelta(0)` のときだけ `"PT0S"` を返す
   - それ以外の値は元の関数 `_original_timedeltaformat` に委譲する

2. `openleadr.messaging` 内で Jinja2 フィルタとして登録されている `TEMPLATES.filters['timedeltaformat']` も、同じラッパー関数に差し替える

これにより、`timedelta(0)` → `"PT0S"` を返すように挙動を修正できます。

---

## パッチの適応

openleadr を利用するアプリケーションのエントリポイント（例: main.py）では、適応するモジュールをインポートしてパッチを適応します。

```python

import openleadrimpl.patch.patch_timedelta 

from openleadrimpl import MyOpenADRServer  # パッチ適用後に openleadrimpl をインポート

def main():
    # 後続処理
    ・・・