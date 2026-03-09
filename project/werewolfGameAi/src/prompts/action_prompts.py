"""
行动提示词模板
用于指导 AI 在各种场景下做出决策
"""

from typing import Dict


# 行动提示词模板
ACTION_PROMPTS: Dict[str, str] = {
    "werewolf_choose_target": """当前是夜晚，作为狼人，你需要选择今晚的击杀目标。

你的身份信息：
- 你的玩家编号：{player_id}号
- 你的角色：狼人

已知信息：
- 你的狼队友编号：{werewolf_teammates}
- 可以击杀的目标（非狼人玩家）：{alive_players}
- 当前是第 {round_number} 夜

请分析局势，选择一个击杀目标。考虑以下因素：
1. 优先击杀可能的神职人员（预言家、女巫、猎人）
2. 绝对不能击杀你的狼队友
3. 可以考虑击杀发言积极或分析能力强的玩家
4. 与狼队友保持一致的选择

请以 JSON 格式回复：
{{
    "target_id": 玩家 ID,
    "reason": "选择理由"
}}""",

    "seer_choose_target": """当前是夜晚，作为预言家，你需要选择今晚的查验目标。

你的身份信息：
- 你的玩家编号：{player_id}号
- 你的角色：预言家

已知信息：
- 可以查验的玩家（未查验过的存活玩家）：{alive_players}
- 当前是第 {round_number} 夜
- 你之前的查验记录：{previous_checks}

请分析局势，选择一个查验目标。考虑以下因素：
1. 优先查验行为可疑的玩家
2. 避免重复查验已经查验过的玩家
3. 可以查验跳身份的 player 验证真伪
4. 考虑查验可能的神职人员以确认队友

请以 JSON 格式回复：
{{
    "target_id": 玩家 ID,
    "reason": "选择理由"
}}""",

    "witch_make_decision": """当前是夜晚，作为女巫，你需要决定是否使用药剂。

你的身份信息：
- 你的玩家编号：{player_id}号
- 你的角色：女巫

已知信息：
- 存活玩家：{alive_players}
- 今晚被狼人击杀的目标：{death_info}
- 你的解药是否可用：{has_save_potion}
- 你的毒药是否可用：{has_poison_potion}
- 当前是第 {round_number} 夜

请分析局势，做出决策：
1. 是否使用解药救今晚的死者（注意：首夜通常建议救人）
2. 是否使用毒药毒死一名玩家（谨慎使用，避免误毒好人）
3. 考虑隐藏身份，避免暴露女巫身份

请以 JSON 格式回复：
{{
    "use_save": true/false,
    "save_target": 玩家 ID 或 null,
    "use_poison": true/false,
    "poison_target": 玩家 ID 或 null,
    "reason": "决策理由"
}}""",

    "day_speech": """当前是白天，轮到你发言。

你的身份信息：
- 你的玩家编号：{player_id}号
- 你的姓名：{player_name}
- 你的角色：{role}
- 你的阵营：{team}

游戏信息：
- 当前是第 {round_number} 天
- 昨晚死亡玩家：{deaths_last_night}
- 存活玩家：{alive_players}

历史重要事件记录：
{important_events}

你的记忆/已知信息：{memories}

请根据以上信息进行发言。发言要求：
1. 符合你的角色身份和立场
2. 如果是狼人，注意隐藏身份
3. 如果是有信息的神职，可以适当透露
4. 分析场上形势，提供有价值的观点
5. **发言长度严格控制在 150-250 字以内**（确保完整显示，不要超出）
6. 记住你是{player_id}号玩家，不要混淆
7. 发言要自然流畅，像真人玩家一样思考
8. **结合历史事件进行分析**（如之前的查验、投票结果等）
9. **重要：发言不要超过 250 字，否则会被截断**

请直接返回你的发言内容（不需要 JSON 格式）。""",

    "vote_target": """当前是投票阶段，你需要选择投票目标。

你的身份信息：
- 你的玩家编号：{player_id}号
- 你的角色：{role}
- 你的阵营：{team}

已知信息：
- 当前是第 {round_number} 天
- 存活玩家：{alive_players}
- 今天的发言记录：{discussions}

历史重要事件记录：
{important_events}

请分析局势，选择投票目标。投票策略：
1. **必须投票** - 除非真的无法判断，否则不要弃票
2. 根据发言内容判断：
   - 发言模糊、划水的玩家可能是狼人
   - 逻辑混乱、前后矛盾的玩家可疑
   - 不敢正面回应问题的玩家有问题
3. 参考其他玩家的分析：
   - 大多数人都怀疑的玩家优先投票
   - 注意狼队友可能故意带节奏
4. 作为好人的投票原则：
   - 宁可投错也不能让狼人安全出局
   - 第一晚可以根据感觉和状态投票
   - 有查验信息时优先相信查验
5. **结合历史事件**（如之前的投票结果、查验信息等）

请以 JSON 格式回复：
{{
    "vote_target": 玩家 ID,
    "reason": "投票理由（详细说明为什么投这个玩家）"
}}

注意：
- 尽量不要弃票（null），必须做出选择
- 即使不确定也要根据发言状态选择一个目标
- 弃票会让好人失去放逐狼人的机会""",

    "hunter_skill": """你是一名即将死亡的猎人，可以发动技能带走一名玩家。

已知信息：
- 存活玩家：{alive_players}
- 你认为的可疑玩家：{suspects}

请分析局势，选择是否发动技能以及带走谁。考虑以下因素：
1. 优先带走疑似狼人的玩家
2. 如果没有明确目标，可以选择不发动技能
3. 避免带走明显的好人

请以 JSON 格式回复：
{{
    "use_skill": true/false,
    "target_id": 玩家 ID 或 null,
    "reason": "选择理由"
}}""",
}


def get_action_prompt(action_type: str, **kwargs) -> str:
    """
    获取行动提示词

    Args:
        action_type: 行动类型
        **kwargs: 用于格式化提示词的参数

    Returns:
        格式化后的提示词
    """
    prompt_template = ACTION_PROMPTS.get(action_type, "")
    if not prompt_template:
        return ""

    # 格式化提示词
    return prompt_template.format(**kwargs)
