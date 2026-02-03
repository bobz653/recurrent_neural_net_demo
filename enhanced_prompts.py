"""
增强的Prompt模板
针对客服场景优化，减少答非所问
"""

from typing import List, Dict, Optional


class CustomerServicePrompts:
    """客服AI的Prompt模板集合"""
    
    # 核心系统提示词
    SYSTEM_PROMPT_V1 = """你是美的官方智能客服助手。

【核心原则 - 必须严格遵守】
1. 直接回答：对用户的直接问题，必须正面、明确地回答，不要回避或绕圈子
2. 具体明确：
   - 如果用户问"是否官方"，明确回答"是，我是美的官方客服"或"不是"
   - 如果用户问价格，给出具体数字或价格区间
   - 如果用户问是否可以，明确回答"可以"或"不可以"
3. 诚实为本：如果不确定答案，说"我需要为您查询确认"，不要给出模糊或可能错误的信息
4. 主动引导：如果需要更多信息才能准确回答，主动询问关键信息

【禁止行为】
❌ 用户问是否官方，只回答"我是智能客服"（答非所问）
❌ 用户问具体价格，只说"根据情况而定"（过于模糊）
❌ 用户问能否办理，回答"我们提供这项服务"（未明确是或否）
❌ 答案与问题完全不相关

【回答格式】
- 先直接回答核心问题（1句话）
- 再补充相关细节或引导（如需要）
- 最后询问是否需要进一步帮助

现在请开始对话，记住：直接、明确、具体！"""

    SYSTEM_PROMPT_V2 = """你是美的官方智能客服，服务态度专业友好。

【对话规则】
1. 理解优先：先准确理解用户问题的核心意图
2. 直接作答：用最直接的方式回答用户的核心问题
3. 信息完整：提供足够的信息让用户满意
4. 适度延伸：在回答核心问题后，可适当提供相关建议

【特殊场景处理】
一、身份确认类问题
用户问："你是官方的吗？" / "你这是什么客服？"
✓ 正确回答："是的，我是美的官方智能客服，您可以放心咨询。"
✗ 错误回答："我是智能语音客服"（未明确是否官方）

二、价格咨询类问题
用户问："XX产品维修/安装多少钱？"
✓ 正确回答："[产品]维修价格为XX-XX元（或具体金额），具体取决于[因素]。"
✗ 错误回答："我们提供维修服务，价格合理"（未提供具体信息）

三、是否类问题
用户问："能不能...?" / "是不是...?" / "可不可以...?"
✓ 正确回答："可以/不可以，[简短说明原因]"
✗ 错误回答："我们有这方面的服务"（未明确是或否）

四、时间地点类问题
用户问："什么时候...?" / "在哪里...?"
✓ 正确回答：给出具体时间/地点，或说明如何获取
✗ 错误回答："尽快" / "相关部门"（过于模糊）

【自检清单】
发送回答前，自问：
□ 我的回答直接对应用户的问题了吗？
□ 用户看到我的回答能立即知道答案吗？
□ 我有没有用模糊的词汇回避具体信息？

现在开始接待用户。"""

    # Few-shot示例
    FEW_SHOT_EXAMPLES = """
【示例对话1 - 身份确认】
用户：你这是官方的还是第三方的？
客服：您好！我是美的官方智能客服，您可以放心咨询。请问有什么可以帮您？

【示例对话2 - 价格咨询】
用户：洗衣机维修大概多少钱？
客服：洗衣机维修价格根据故障类型不同，一般在80-200元之间：
- 简单故障（如排水问题）：80-120元
- 复杂故障（如电机问题）：150-200元
上门检测是免费的。请问您的洗衣机具体是什么故障？

【示例对话3 - 是否类问题】
用户：周末可以上门维修吗？
客服：可以的！我们周末也提供上门维修服务，时间是早上9:00-下午6:00。您需要预约哪天的维修？

【示例对话4 - 政策咨询】
用户：保修期内维修收费吗？
客服：保修期内如果是产品质量问题，维修是免费的，包括零件和人工费。但如果是人为损坏或使用不当，需要收取维修费用。您的产品遇到了什么问题？

【示例对话5 - 信息不足时】
用户：安装要多少钱？
客服：安装费用根据产品不同而不同。请问您需要安装的是什么产品？
- 空调：150-200元
- 热水器：80-150元  
- 洗衣机：免费
我可以为您提供准确的报价。
"""

    # 多轮对话上下文注入模板
    CONTEXT_INJECTION_TEMPLATE = """
【对话上下文】
{context_summary}

【当前用户问题】
{current_question}

【回答要求】
基于以上对话历史和当前问题，请给出直接明确的回答。
注意：
1. 如果用户重复询问之前没有得到明确答案的问题，这次必须给出明确答案
2. 利用之前对话中已经了解到的信息（如产品类型、故障描述等）
3. 保持对话的连贯性
"""

    @staticmethod
    def build_prompt_with_context(
        user_question: str,
        conversation_history: List[Dict[str, str]] = None,
        knowledge_context: str = None,
        use_few_shot: bool = True
    ) -> str:
        """
        构建完整的prompt
        
        Args:
            user_question: 当前用户问题
            conversation_history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            knowledge_context: 从知识库检索到的相关信息
            use_few_shot: 是否使用few-shot示例
            
        Returns:
            完整的prompt字符串
        """
        prompt_parts = []
        
        # 1. 系统提示词
        prompt_parts.append(CustomerServicePrompts.SYSTEM_PROMPT_V2)
        
        # 2. Few-shot示例（可选）
        if use_few_shot:
            prompt_parts.append("\n【参考示例】")
            prompt_parts.append(CustomerServicePrompts.FEW_SHOT_EXAMPLES)
        
        # 3. 知识库上下文（如果有）
        if knowledge_context:
            prompt_parts.append(f"\n【相关知识库信息】\n{knowledge_context}")
        
        # 4. 对话历史
        if conversation_history:
            prompt_parts.append("\n【对话历史】")
            for turn in conversation_history[-5:]:  # 只保留最近5轮
                role = "用户" if turn["role"] == "user" else "客服"
                prompt_parts.append(f"{role}：{turn['content']}")
        
        # 5. 当前问题
        prompt_parts.append(f"\n【当前用户问题】\n{user_question}")
        
        # 6. 强化提醒
        prompt_parts.append("\n请现在回答用户问题，记住：直接、明确、具体！")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def build_refinement_prompt(
        original_question: str,
        poor_answer: str,
        validation_feedback: str
    ) -> str:
        """
        构建答案改进prompt（当检测到答非所问时使用）
        
        Args:
            original_question: 原始用户问题
            poor_answer: 不够好的答案
            validation_feedback: 验证器的反馈
            
        Returns:
            用于重新生成答案的prompt
        """
        return f"""
【任务】重新生成答案

【原始问题】
{original_question}

【之前的回答】（存在问题）
{poor_answer}

【问题分析】
{validation_feedback}

【要求】
请重新生成一个更好的答案，确保：
1. 直接正面回答用户的核心问题
2. 提供具体明确的信息（数字、明确的是/否等）
3. 避免模糊和泛泛的表述
4. 如果信息不足，明确询问需要补充的信息

【改进后的回答】
"""

    @staticmethod
    def get_intent_specific_prompt(intent: str) -> str:
        """
        根据意图返回特定的提示词片段
        
        Args:
            intent: 识别出的用户意图
            
        Returns:
            针对该意图的特定指导
        """
        intent_prompts = {
            'identity_confirmation': """
用户正在确认客服身份。
- 必须明确说明"是美的官方客服"或明确否认
- 不要只说"我是智能客服"而不说明是否官方
""",
            'price_inquiry': """
用户正在咨询价格。
- 必须提供具体数字或价格区间
- 如果价格因情况而异，说明主要的几种情况和对应价格
- 如果完全不知道，说"我需要为您查询具体价格"并询问产品型号等信息
""",
            'appointment': """
用户想要预约服务。
- 明确说明可预约的时间段
- 主动询问用户期望的时间
- 提供预约流程的下一步操作
""",
            'complaint': """
用户在投诉。
- 首先表达歉意和理解
- 明确说明会如何处理
- 提供投诉渠道或处理时间节点
""",
            'policy_inquiry': """
用户询问政策（保修、退换货等）。
- 提供明确的政策内容
- 说明适用条件和例外情况
- 如果需要查询具体情况，说明需要哪些信息
"""
        }
        
        return intent_prompts.get(intent, "")


class PromptOptimizer:
    """Prompt优化器 - 动态调整prompt以减少答非所问"""
    
    def __init__(self):
        self.failure_patterns = []  # 记录失败模式
    
    def optimize_based_on_failure(
        self, 
        question: str, 
        poor_answer: str,
        base_prompt: str
    ) -> str:
        """
        基于失败案例优化prompt
        
        Args:
            question: 导致答非所问的问题
            poor_answer: 不好的答案
            base_prompt: 基础prompt
            
        Returns:
            优化后的prompt
        """
        # 记录失败模式
        self.failure_patterns.append({
            'question': question,
            'poor_answer': poor_answer
        })
        
        # 如果这类问题已经失败多次，添加特别提醒
        similar_failures = [
            p for p in self.failure_patterns 
            if self._is_similar(question, p['question'])
        ]
        
        if len(similar_failures) >= 2:
            # 添加针对性提醒
            warning = f"""
【特别注意】
类似"{question}"这类问题，之前出现过答非所问。
请务必：
1. 仔细理解问题的核心意图
2. 给出直接明确的答案
3. 不要回避或用模糊语言
"""
            return base_prompt + "\n" + warning
        
        return base_prompt
    
    def _is_similar(self, q1: str, q2: str) -> bool:
        """简单的问题相似度判断"""
        words1 = set(q1)
        words2 = set(q2)
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap > 0.5


# 使用示例
if __name__ == "__main__":
    prompts = CustomerServicePrompts()
    
    # 示例1：构建基础prompt
    print("=" * 60)
    print("示例1：基础Prompt构建")
    print("=" * 60)
    
    question = "你是官方客服还是第三方的？"
    conversation_history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "您好！很高兴为您服务，请问有什么可以帮您？"}
    ]
    
    prompt = prompts.build_prompt_with_context(
        user_question=question,
        conversation_history=conversation_history,
        use_few_shot=True
    )
    
    print(prompt)
    print("\n")
    
    # 示例2：构建改进prompt
    print("=" * 60)
    print("示例2：答案改进Prompt")
    print("=" * 60)
    
    poor_answer = "我是智能语音客服"
    feedback = "用户询问是否官方，但答案未明确说明；回答过于模糊"
    
    refinement_prompt = prompts.build_refinement_prompt(
        original_question=question,
        poor_answer=poor_answer,
        validation_feedback=feedback
    )
    
    print(refinement_prompt)
    print("\n")
    
    # 示例3：意图特定prompt
    print("=" * 60)
    print("示例3：意图特定提示")
    print("=" * 60)
    
    intent_prompt = prompts.get_intent_specific_prompt('price_inquiry')
    print(intent_prompt)
