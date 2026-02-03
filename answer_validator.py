"""
答案相关性验证器
用于检测AI回答是否真正回答了用户的问题，避免答非所问
"""

import re
from typing import Tuple, Dict, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    score: float  # 0-1之间
    reason: str
    suggestions: List[str]


class AnswerValidator:
    """答案验证器 - 检测答非所问"""
    
    def __init__(self):
        # 定义关键问题类型及其必需的答案特征
        self.question_patterns = {
            'identity_confirmation': {
                'patterns': [r'官方', r'是不是.*的', r'你是谁', r'什么.*客服'],
                'required_in_answer': ['官方', '是', '不是'],
                'forbidden_vague': ['智能客服', '为您服务']  # 单独出现时不够明确
            },
            'price_inquiry': {
                'patterns': [r'多少钱', r'价格', r'费用', r'收费', r'怎么.*收.*费'],
                'required_in_answer': [r'\d+元', r'\d+块', r'免费', r'价格'],
                'forbidden_vague': ['根据情况', '请咨询']
            },
            'yes_no_question': {
                'patterns': [r'是不是', r'是否', r'可不可以', r'能不能', r'要不要'],
                'required_in_answer': ['是', '否', '可以', '不可以', '需要', '不需要'],
                'forbidden_vague': []
            },
            'specific_info': {
                'patterns': [r'什么时候', r'在哪', r'如何', r'怎么'],
                'required_in_answer': [],  # 动态检查
                'forbidden_vague': ['稍后', '相关人员', '尽快']
            }
        }
    
    def validate(self, question: str, answer: str) -> ValidationResult:
        """
        验证答案是否回答了问题
        
        Args:
            question: 用户问题
            answer: AI回答
            
        Returns:
            ValidationResult: 验证结果
        """
        # 识别问题类型
        question_type = self._identify_question_type(question)
        
        if question_type is None:
            # 无法识别问题类型，进行通用检查
            return self._generic_validation(question, answer)
        
        # 针对特定问题类型验证
        return self._type_specific_validation(question, answer, question_type)
    
    def _identify_question_type(self, question: str) -> str:
        """识别问题类型"""
        for q_type, config in self.question_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, question):
                    return q_type
        return None
    
    def _type_specific_validation(
        self, 
        question: str, 
        answer: str, 
        question_type: str
    ) -> ValidationResult:
        """针对特定类型问题的验证"""
        config = self.question_patterns[question_type]
        score = 1.0
        issues = []
        suggestions = []
        
        # 检查是否包含必需元素
        required = config.get('required_in_answer', [])
        if required:
            has_required = False
            for req in required:
                if isinstance(req, str):
                    if req in answer:
                        has_required = True
                        break
                else:  # 正则表达式
                    if re.search(req, answer):
                        has_required = True
                        break
            
            if not has_required:
                score -= 0.5
                issues.append(f"答案中缺少必要信息：{', '.join(required)}")
                suggestions.append(f"应明确包含：{', '.join(str(r) for r in required[:2])}")
        
        # 检查是否存在模糊回答
        forbidden = config.get('forbidden_vague', [])
        vague_found = []
        for vague_term in forbidden:
            if vague_term in answer:
                # 检查是否有其他明确信息
                if not any(req in answer for req in required if isinstance(req, str)):
                    vague_found.append(vague_term)
        
        if vague_found:
            score -= 0.3
            issues.append(f"回答过于模糊：{', '.join(vague_found)}")
            suggestions.append("应提供更具体明确的信息")
        
        # 特殊检查：身份确认问题
        if question_type == 'identity_confirmation':
            if '官方' in question and '官方' not in answer:
                score -= 0.4
                issues.append("用户问是否官方，但答案未明确说明")
                suggestions.append("应明确回答'是美的官方客服'或'不是官方'")
        
        # 特殊检查：价格问题
        if question_type == 'price_inquiry':
            # 检查是否有具体数字或明确的免费说明
            has_number = re.search(r'\d+', answer)
            has_free = '免费' in answer
            if not has_number and not has_free:
                score -= 0.4
                issues.append("价格问题未提供具体数字")
                suggestions.append("应提供具体价格数字或明确说明免费")
        
        # 检查答案长度（过短可能信息不足）
        if len(answer) < 10:
            score -= 0.2
            issues.append("答案过短，可能信息不足")
        
        is_valid = score >= 0.6
        reason = "; ".join(issues) if issues else "答案恰当"
        
        return ValidationResult(
            is_valid=is_valid,
            score=max(0.0, min(1.0, score)),
            reason=reason,
            suggestions=suggestions
        )
    
    def _generic_validation(self, question: str, answer: str) -> ValidationResult:
        """通用验证（无法识别具体类型时）"""
        score = 0.8  # 基础分
        issues = []
        suggestions = []
        
        # 基本长度检查
        if len(answer) < 5:
            score -= 0.3
            issues.append("答案过短")
        
        # 检查是否完全不相关（基于关键词重叠）
        question_words = set(re.findall(r'[\u4e00-\u9fa5]+', question))
        answer_words = set(re.findall(r'[\u4e00-\u9fa5]+', answer))
        
        overlap = len(question_words & answer_words)
        if overlap == 0 and len(question_words) > 2:
            score -= 0.4
            issues.append("答案与问题关键词无重叠，可能不相关")
            suggestions.append("确保回答与用户问题相关")
        
        reason = "; ".join(issues) if issues else "基本符合要求"
        return ValidationResult(
            is_valid=score >= 0.5,
            score=score,
            reason=reason,
            suggestions=suggestions
        )
    
    def suggest_improvement(self, question: str, answer: str) -> str:
        """
        基于验证结果，建议改进方向
        
        Returns:
            改进建议的提示词
        """
        result = self.validate(question, answer)
        
        if result.is_valid:
            return None
        
        improvement_prompt = f"""
原始回答存在问题：{result.reason}

改进建议：
{chr(10).join(f"- {s}" for s in result.suggestions)}

请重新生成答案，注意：
1. 直接明确地回答用户的问题
2. 避免模糊和泛泛的表述
3. 提供具体信息（数字、明确的是/否等）

用户问题：{question}
"""
        return improvement_prompt


class DialogueStateTracker:
    """对话状态追踪器 - 管理多轮对话上下文"""
    
    def __init__(self):
        self.history: List[Dict] = []
        self.current_intent: str = None
        self.slots: Dict = {}
        self.unanswered_questions: List[str] = []
    
    def update(self, user_input: str, bot_response: str, intent: str = None):
        """更新对话状态"""
        self.history.append({
            'user': user_input,
            'bot': bot_response,
            'intent': intent
        })
        
        if intent:
            self.current_intent = intent
        
        # 检查是否有未回答的问题
        validator = AnswerValidator()
        result = validator.validate(user_input, bot_response)
        if not result.is_valid:
            self.unanswered_questions.append(user_input)
    
    def get_context_summary(self) -> str:
        """获取上下文摘要，用于注入prompt"""
        if not self.history:
            return "新对话开始"
        
        summary_parts = []
        
        # 当前意图
        if self.current_intent:
            summary_parts.append(f"当前意图：{self.current_intent}")
        
        # 已收集的槽位信息
        if self.slots:
            slots_str = ", ".join(f"{k}={v}" for k, v in self.slots.items())
            summary_parts.append(f"已知信息：{slots_str}")
        
        # 未回答的问题
        if self.unanswered_questions:
            summary_parts.append(f"用户关心但未充分回答的问题：{self.unanswered_questions[-1]}")
        
        # 最近的对话
        recent = self.history[-3:]
        history_str = "\n".join(
            f"用户：{turn['user']}\n客服：{turn['bot']}" 
            for turn in recent
        )
        summary_parts.append(f"最近对话：\n{history_str}")
        
        return "\n\n".join(summary_parts)
    
    def clear(self):
        """清空状态（新对话）"""
        self.history.clear()
        self.current_intent = None
        self.slots.clear()
        self.unanswered_questions.clear()


# 使用示例
if __name__ == "__main__":
    validator = AnswerValidator()
    
    # 测试案例1：身份确认问题
    print("=" * 50)
    print("测试1: 身份确认问题")
    q1 = "你这是官方的还是什么的？"
    a1_bad = "我是智能语音客服"
    a1_good = "是的，我是美的官方智能客服，您可以放心咨询"
    
    result_bad = validator.validate(q1, a1_bad)
    print(f"问题: {q1}")
    print(f"回答: {a1_bad}")
    print(f"验证结果: {'✓通过' if result_bad.is_valid else '✗未通过'}")
    print(f"分数: {result_bad.score:.2f}")
    print(f"原因: {result_bad.reason}")
    print(f"建议: {result_bad.suggestions}")
    
    print("\n" + "-" * 50 + "\n")
    
    result_good = validator.validate(q1, a1_good)
    print(f"问题: {q1}")
    print(f"回答: {a1_good}")
    print(f"验证结果: {'✓通过' if result_good.is_valid else '✗未通过'}")
    print(f"分数: {result_good.score:.2f}")
    
    # 测试案例2：价格问题
    print("\n" + "=" * 50)
    print("测试2: 价格问题")
    q2 = "洗衣机维修多少钱？"
    a2_bad = "我们提供专业的维修服务，具体请咨询"
    a2_good = "洗衣机维修价格在80-200元之间，具体取决于故障类型。请问是什么故障？"
    
    result_bad2 = validator.validate(q2, a2_bad)
    print(f"问题: {q2}")
    print(f"回答: {a2_bad}")
    print(f"验证结果: {'✓通过' if result_bad2.is_valid else '✗未通过'}")
    print(f"分数: {result_bad2.score:.2f}")
    print(f"原因: {result_bad2.reason}")
    
    print("\n" + "-" * 50 + "\n")
    
    result_good2 = validator.validate(q2, a2_good)
    print(f"问题: {q2}")
    print(f"回答: {a2_good}")
    print(f"验证结果: {'✓通过' if result_good2.is_valid else '✗未通过'}")
    print(f"分数: {result_good2.score:.2f}")
    
    # 测试改进建议
    print("\n" + "=" * 50)
    print("改进建议:")
    improvement = validator.suggest_improvement(q2, a2_bad)
    print(improvement)
