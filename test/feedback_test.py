import sys
from pathlib import Path

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from modules.SXMPycontroller import STSScript, SXMController
from modules.SXMRemote import DDEClient


def main():
    stm = SXMController(debug_mode=True)
    print("current feedback:", stm.FbOn)
    stm.get_feedback_state()
    print("current feedback after updated:", stm.FbOn)
    stm.feedback_on()
    print("current feedback after on:", stm.FbOn)
    # stm.get_feedback_state()
    # print("current feedback after updated:", stm.FbOn)
    stm.feedback_off()
    print("current feedback after close:", stm.FbOn)
    stm.feedback_on()
    print("current feedback after reon:", stm.FbOn)

    # stm = DDEClient("SXM", "Remote")
    # a = None
    # a = stm.GetFeedbackPara('Enable')
    # print("original feedback:", a)

    # # stm.SendWait("FeedPara('Enable', 0);")
    # # a= stm.GetFeedbackPara('Enable')
    # # print("current feedback after on1:", a)

    # stm.SendWait("FeedPara('Enable', 0);")
    # # a= stm.GetFeedbackPara('Enable')
    # # print("current feedback after on2:", a)

    # # stm.SendWait("FeedPara('Enable', 1);")
    # # a = stm.GetFeedbackPara('Enable')
    # # print("current feedback after off1:", a)

    # stm.SendWait("FeedPara('Enable', 1);")
    # a = stm.GetFeedbackPara('Enable')
    # print("current feedback after off2:", a)

    # stm.SendWait("FeedPara('Enable', 0);")
    # a = stm.GetFeedbackPara('Enable')
    # print("current feedback after reon1:", a)

    # stm.SendWait("FeedPara('Enable', 0);")
    # a = stm.GetFeedbackPara('Enable')
    # print("current feedback after reon2:", a)

if __name__ == "__main__":
    main()