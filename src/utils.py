# src/utils.py
import os
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

def fix_korean(col):
    """
    Decodes a column from latin1 to cp949 to fix broken Korean characters.
    """
    try:
        if col.dtype == 'object':
            return col.str.decode('latin1').str.encode('cp949').str.decode('cp949')
    except Exception:
        return col
    return col

def add_north_arrow(ax, x=0.95, y=0.95, size=0.05, lw=1.5):
    """
    Adds a north arrow to a matplotlib axes object.
    """
    ax.arrow(x, y, 0, size, transform=ax.transAxes,
             head_width=size*0.8, head_length=size*0.9,
             fc='black', ec='black', lw=lw)
    ax.text(x, y - size*1.5, 'N', transform=ax.transAxes,
            ha='center', va='center', fontsize='large', fontweight='bold')

def add_scale_bar(ax, length=100000):
    """
    Adds a scale bar to a matplotlib axes object.
    """
    scalebar = ScaleBar(1, "m", length_fraction=0.25, location='lower right',
                        box_alpha=0.75, pad=0.5, border_pad=0.5)
    ax.add_artist(scalebar)

def ensure_dir(directory_path):
    """
    Ensures that a directory exists; if not, it creates it.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")