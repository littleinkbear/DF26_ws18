"""prints 共用底座 —— notebook 里学生看到的文字都从这里出。
=================================================================
_say  = 薄薄一层 print(不加前缀):每个 prints.* 只管「说什么」,不管「怎么印」。
        将来要加前缀 / 落盘 / 静音,只改这一处。
_try  = 韧性包装:一段回报出错就跳过(印一行 skip),不炸掉整个 func。
        每个 prints.* 把每一行(或每一圈循环)包进 _try,能印的照印、坏的略过。
ready = setup 格最后一行的就绪回报:确认引擎已载入、现在跑哪个站点。
"""


def _say(*args):
    """所有回报统一走这里(等同 print,单一出口好维护)。"""
    print(*args)


def _try(fn, what=""):
    """跑一小段回报;出错就跳过(印一行 skip),让后面的行照常跑。
    fn = 无参 callable,里面自己 _say;what = 出错时标注这段在做什么。"""
    try:
        fn()
    except Exception as e:
        try:
            _say("  (跳过%s:%s: %s)" % (what, type(e).__name__, e))
        except Exception:
            pass  # 连 skip 提示都印不出(怪异 console 编码)也别炸


def ready():
    """setup 格跑完的就绪回报:引擎已载入,当前站点是谁(改 config.SLUG 换站)。"""
    import config
    _try(lambda: _say("引擎就绪 · 当前站点:%s(%s)" % (config.site_name(), config.SLUG)), "就绪回报")
