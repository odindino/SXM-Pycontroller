# 添加主程式目錄到系統路徑
from pathlib import Path
import sys
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
from utils.SXMPyPlot import generate_auto_move_preview

import plotly.io as pio

class SXMPreviewTester:
    def test_auto_move_preview(self):
        # Set the test parameters
        center_x = 250
        center_y = 250
        scan_range = 500
        scan_angle = 60
        movement_script = 'RULLDDRR'

        # Generate the preview plot
        preview_plot = generate_auto_move_preview(
            center_x, center_y, scan_range, scan_angle, movement_script
        )

        # Render the plot (you can use this in your GUI)
        pio.show(preview_plot)

# Run the test
tester = SXMPreviewTester()
tester.test_auto_move_preview()