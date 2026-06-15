"""Pick a CJK-capable font for matplotlib (Linux servers often lack PingFang/SimHei)."""

from __future__ import annotations

from pathlib import Path

_SKILL_FONTS = Path(__file__).resolve().parent / "fonts"

_cached_font_prop = None

_SYSTEM_CJK_NAMES = (
    "Noto Sans CJK SC",
    "Noto Sans SC",
    "Noto Sans CJK TC",
    "WenQuanYi Micro Hei",
    "WenQuanYi Zen Hei",
    "Source Han Sans SC",
    "Source Han Sans CN",
    "AR PL UMing CN",
    "PingFang SC",
    "Heiti SC",
    "STHeiti",
    "SimHei",
    "Microsoft YaHei",
)


def get_cjk_font_path() -> Path | None:
    bundled: list[Path] = []
    for pattern in ("*.otf", "*.ttf", "*.OTF", "*.TTF"):
        bundled.extend(_SKILL_FONTS.glob(pattern))
    if not bundled:
        return None
    for path in sorted(bundled):
        name = path.name.lower()
        if "cjk" in name or "cjksc" in name:
            return path
    return sorted(bundled)[0]


def get_cjk_font_properties():
    """FontProperties bound to bundled font file (reliable on Linux)."""
    global _cached_font_prop
    if _cached_font_prop is not None:
        return _cached_font_prop

    from matplotlib import font_manager as fm

    path = get_cjk_font_path()
    if path is not None:
        try:
            fm.fontManager.addfont(str(path))
            prop = fm.FontProperties(fname=str(path))
            _cached_font_prop = prop
            return prop
        except Exception:
            pass
    for name in _SYSTEM_CJK_NAMES:
        try:
            prop = fm.FontProperties(family=name)
            _cached_font_prop = prop
            return prop
        except Exception:
            continue
    return None


def configure_matplotlib_cjk(plt) -> None:
    prop = get_cjk_font_properties()
    if prop is not None:
        family = prop.get_name()
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [family, "DejaVu Sans", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False


def apply_font_to_figure(fig, font_prop) -> None:
    if font_prop is None:
        return
    for ax in fig.axes:
        title = ax.get_title()
        if title:
            ax.set_title(title, fontproperties=font_prop)
        xlabel = ax.get_xlabel()
        if xlabel:
            ax.set_xlabel(xlabel, fontproperties=font_prop)
        ylabel = ax.get_ylabel()
        if ylabel:
            ax.set_ylabel(ylabel, fontproperties=font_prop)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)
        for text in ax.texts:
            text.set_fontproperties(font_prop)
    if getattr(fig, "_suptitle", None) is not None and fig._suptitle:
        try:
            fig._suptitle.set_fontproperties(font_prop)
        except Exception:
            pass
