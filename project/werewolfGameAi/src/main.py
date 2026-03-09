"""
狼人杀 AI 游戏系统 - 上帝视角观测模式
用户只控制：开始、投票、下一轮
其余全部 AI 自动进行
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from cli.game_viewer import GameViewer
from llm.config import LLMConfig


def main():
    """主函数"""
    print("=" * 70)
    print("狼人杀 AI 游戏系统 - 上帝视角观测模式")
    print("=" * 70)
    print()
    print("游戏说明:")
    print("  - 9 个 AI 玩家自动进行对局")
    print("  - 您以上帝视角观测完整流程")
    print("  - 您可以控制：开始游戏、开启投票、进入下一轮")
    print()

    # 检查环境变量
    import os
    if not os.getenv("LLM_API_KEY"):
        print("[提示] 未设置 LLM_API_KEY 环境变量")
        print("将进入测试模式（跳过 AI 调用）")
        print()

    # 创建游戏查看器
    viewer = GameViewer()

    print("正在初始化游戏...")
    viewer.setup_game()
    print("[OK] 游戏初始化完成\n")

    # 显示初始状态
    viewer.display.print_header("初始玩家状态")
    viewer.display.display_player_status(viewer.state)

    print("\n准备就绪，按回车键开始游戏...")
    input()


    # 运行游戏
    try:
        asyncio.run(viewer.run_game())
    except KeyboardInterrupt:
        print("\n\n[系统] 游戏已中断")
    except Exception as e:
        print(f"\n[错误] 游戏异常：{e}")
        
        raise


if __name__ == "__main__":
    main()
