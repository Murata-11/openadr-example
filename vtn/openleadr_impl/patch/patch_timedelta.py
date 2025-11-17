from datetime import timedelta
from openleadr import utils
from openleadr import messaging

_original_timedeltaformat = utils.timedeltaformat

def timedeltaformat_with_zero(value):
    """
    timedelta を OpenADR / RFC5545 形式の duration 文字列に変換するラッパー関数。

    - ゼロ期間 (timedelta(0)) の場合のみ "PT0S" を返し、
      それ以外は元の openleadr 実装に委譲する。
    """

    if not isinstance(value, timedelta):
        return value

    # total_seconds() が 0 の場合、元の実装では "P" のような不正な文字列になるため
    # 明示的に "PT0S" を返すように上書きする
    if value.total_seconds() == 0:
        return "PT0S"

    # ゼロ以外の timedelta は元の実装に任せる
    return _original_timedeltaformat(value)

utils.timedeltaformat = timedeltaformat_with_zero

# openleadr.messaging では、TEMPLATES.filters['timedeltaformat'] に
# utils.timedeltaformat が登録されているため、
# すでに生成済みのフィルタを上書きしておく必要がある
messaging.TEMPLATES.filters['timedeltaformat'] = timedeltaformat_with_zero