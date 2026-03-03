import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

def setup_cjk_font():
    candidates = [
        # Windows
        "Microsoft JhengHei", "Microsoft YaHei",
        # macOS
        "PingFang TC", "Heiti TC", "Songti TC",
        # Linux
        "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans CJK JP",
        "WenQuanYi Zen Hei", "AR PL UMing TW", "AR PL UMing CN",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break

    plt.rcParams["axes.unicode_minus"] = False