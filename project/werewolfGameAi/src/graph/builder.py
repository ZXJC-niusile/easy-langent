"""
LangGraph StateGraph 构建器
定义游戏流程的状态转换
"""

from langgraph.graph import StateGraph, START, END
from models.game_state import GameState
from graph.nodes import GameNodes


def create_game_graph(agent_manager=None) -> StateGraph:
    """
    创建狼人杀游戏状态图

    Args:
        agent_manager: Agent 管理器，用于调用各角色 AI

    Returns:
        编译好的 StateGraph
    """
    # 创建节点实例
    nodes = GameNodes(agent_manager)

    # 创建状态图
    builder = StateGraph(GameState)

    # 添加所有节点
    builder.add_node("start_game", nodes.start_game)
    builder.add_node("night_werewolf", nodes.night_werewolf_action)
    builder.add_node("night_seer", nodes.night_seer_action)
    builder.add_node("night_witch", nodes.night_witch_action)
    builder.add_node("night_end", nodes.night_end)
    builder.add_node("day_start", nodes.day_start)
    builder.add_node("day_discussion", nodes.day_discussion)
    builder.add_node("day_voting", nodes.day_voting)
    builder.add_node("day_end", nodes.day_end)

    # 定义边（流程）
    # 游戏开始
    builder.add_edge(START, "start_game")
    builder.add_edge("start_game", "night_werewolf")

    # 夜晚流程
    builder.add_edge("night_werewolf", "night_seer")
    builder.add_edge("night_seer", "night_witch")
    builder.add_edge("night_witch", "night_end")

    # 夜晚结束 -> 白天开始
    builder.add_edge("night_end", "day_start")

    # 白天流程
    builder.add_edge("day_start", "day_discussion")
    builder.add_edge("day_discussion", "day_voting")
    builder.add_edge("day_voting", "day_end")

    # 白天结束 -> 检查是否继续
    def should_continue(state: GameState) -> str:
        """条件边判断函数"""
        if state.current_phase.name == "GAME_OVER":
            return END
        return "night_werewolf"

    builder.add_conditional_edges(
        "day_end",
        should_continue,
        {
            END: END,
            "night_werewolf": "night_werewolf",
        },
    )

    # 编译图
    graph = builder.compile()

    return graph
