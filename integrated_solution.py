"""
完整的客服AI解决方案集成
结合答案验证、增强Prompt和RAG系统
"""

from typing import List, Dict, Optional
from answer_validator import AnswerValidator, DialogueStateTracker
from enhanced_prompts import CustomerServicePrompts, PromptOptimizer
from rag_system import RAGSystem, SimpleKnowledgeBase


class ImprovedCustomerServiceAI:
    """
    改进的客服AI系统
    - 集成RAG避免幻觉和模糊回答
    - 使用增强prompt减少答非所问
    - 答案验证和自动改进机制
    """
    
    def __init__(
        self, 
        llm_generate_func,  # 4B模型的生成函数
        enable_rag: bool = True,
        enable_validation: bool = True,
        max_retry: int = 2
    ):
        """
        Args:
            llm_generate_func: LLM生成函数，接收prompt返回答案
            enable_rag: 是否启用RAG
            enable_validation: 是否启用答案验证
            max_retry: 答案不合格时最大重试次数
        """
        self.llm = llm_generate_func
        self.enable_rag = enable_rag
        self.enable_validation = enable_validation
        self.max_retry = max_retry
        
        # 初始化各个组件
        self.rag = RAGSystem() if enable_rag else None
        self.validator = AnswerValidator() if enable_validation else None
        self.state_tracker = DialogueStateTracker()
        self.prompt_optimizer = PromptOptimizer()
        self.prompts = CustomerServicePrompts()
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'validation_failures': 0,
            'retries': 0,
            'rag_used': 0
        }
    
    def chat(
        self, 
        user_input: str,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        处理用户输入，返回答案
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            
        Returns:
            {
                'answer': str,  # 最终答案
                'intent': str,  # 识别的意图
                'validation_passed': bool,  # 是否通过验证
                'retry_count': int,  # 重试次数
                'knowledge_used': bool  # 是否使用了知识库
            }
        """
        self.stats['total_queries'] += 1
        
        # 1. 检索相关知识（如果启用RAG）
        knowledge_context = None
        intent = None
        if self.enable_rag:
            retrieval_result = self.rag.retrieve(user_input)
            knowledge_context = retrieval_result['context_text']
            intent = retrieval_result['intent']
            if knowledge_context:
                self.stats['rag_used'] += 1
        
        # 2. 构建初始prompt
        base_prompt = self.prompts.build_prompt_with_context(
            user_question=user_input,
            conversation_history=conversation_history,
            knowledge_context=knowledge_context,
            use_few_shot=True
        )
        
        # 如果有意图，添加意图特定提示
        if intent:
            intent_prompt = self.prompts.get_intent_specific_prompt(intent)
            if intent_prompt:
                base_prompt += "\n" + intent_prompt
        
        # 3. 生成答案（带重试机制）
        answer = None
        validation_passed = True
        retry_count = 0
        
        for attempt in range(self.max_retry + 1):
            # 生成答案
            if attempt == 0:
                # 第一次尝试
                prompt = base_prompt
            else:
                # 重试：基于验证反馈优化prompt
                retry_count += 1
                self.stats['retries'] += 1
                
                improvement_prompt = self.validator.suggest_improvement(
                    user_input, answer
                )
                prompt = base_prompt + "\n" + improvement_prompt
            
            # 调用LLM生成
            answer = self.llm(prompt)
            
            # 验证答案（如果启用）
            if self.enable_validation:
                validation_result = self.validator.validate(user_input, answer)
                
                if validation_result.is_valid:
                    validation_passed = True
                    break
                else:
                    validation_passed = False
                    self.stats['validation_failures'] += 1
                    
                    # 如果是最后一次尝试，接受当前答案但添加标记
                    if attempt == self.max_retry:
                        # 可以选择添加免责声明或人工介入提示
                        pass
            else:
                break
        
        # 4. 更新对话状态
        self.state_tracker.update(user_input, answer, intent)
        
        # 5. 返回结果
        return {
            'answer': answer,
            'intent': intent,
            'validation_passed': validation_passed,
            'retry_count': retry_count,
            'knowledge_used': knowledge_context is not None
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats['total_queries'] > 0:
            stats['rag_usage_rate'] = stats['rag_used'] / stats['total_queries']
            stats['validation_failure_rate'] = stats['validation_failures'] / stats['total_queries']
            stats['avg_retries'] = stats['retries'] / stats['total_queries']
        return stats
    
    def reset_conversation(self):
        """重置对话状态（开始新对话）"""
        self.state_tracker.clear()


def mock_llm_generate(prompt: str) -> str:
    """
    Mock LLM生成函数（用于演示）
    实际使用时替换为真实的4B模型调用
    """
    # 这里应该调用实际的LLM API
    # 例如: response = model.generate(prompt, max_length=512)
    
    # 为了演示，返回模拟答案
    if "官方" in prompt and "用户问题" in prompt:
        if "你这是官方" in prompt or "你是官方" in prompt:
            return "是的，我是美的官方智能客服，您可以放心咨询。有什么可以帮您？"
    
    if "价格" in prompt or "多少钱" in prompt:
        if "洗衣机" in prompt:
            return "洗衣机维修价格根据故障类型，一般在80-200元之间。请问您的洗衣机是什么故障？"
    
    return "我是美的客服，很高兴为您服务。请问有什么可以帮您？"


# 完整演示
def demo():
    """完整演示改进后的客服AI"""
    
    print("=" * 70)
    print("客服AI答非所问问题解决方案 - 完整演示")
    print("=" * 70)
    
    # 初始化系统
    ai = ImprovedCustomerServiceAI(
        llm_generate_func=mock_llm_generate,
        enable_rag=True,
        enable_validation=True,
        max_retry=2
    )
    
    # 测试案例
    test_cases = [
        {
            'user': "你好",
            'description': "问候"
        },
        {
            'user': "你这是官方的还是什么的？",
            'description': "身份确认（之前答非所问的典型问题）"
        },
        {
            'user': "洗衣机维修大概多少钱？",
            'description': "价格咨询（之前回答模糊的典型问题）"
        },
        {
            'user': "保修期内修理要收费吗？",
            'description': "政策咨询"
        },
    ]
    
    conversation_history = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试案例 {i}: {case['description']}")
        print(f"{'=' * 70}")
        
        user_input = case['user']
        print(f"\n👤 用户: {user_input}")
        
        # 调用AI
        result = ai.chat(user_input, conversation_history)
        
        # 显示结果
        print(f"\n🤖 客服: {result['answer']}")
        
        # 显示元信息
        print(f"\n📊 元信息:")
        print(f"   - 识别意图: {result['intent'] or '未识别'}")
        print(f"   - 使用知识库: {'是' if result['knowledge_used'] else '否'}")
        print(f"   - 验证通过: {'✓' if result['validation_passed'] else '✗'}")
        if result['retry_count'] > 0:
            print(f"   - 重试次数: {result['retry_count']}")
        
        # 更新对话历史
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": result['answer']})
    
    # 显示统计信息
    print(f"\n{'=' * 70}")
    print("系统统计信息")
    print(f"{'=' * 70}")
    stats = ai.get_stats()
    print(f"总查询数: {stats['total_queries']}")
    print(f"RAG使用率: {stats.get('rag_usage_rate', 0):.1%}")
    print(f"验证失败率: {stats.get('validation_failure_rate', 0):.1%}")
    print(f"平均重试次数: {stats.get('avg_retries', 0):.2f}")


def compare_old_vs_new():
    """对比改进前后的效果"""
    
    print("\n" + "=" * 70)
    print("改进前后对比")
    print("=" * 70)
    
    test_cases = [
        {
            'question': "你这是官方的还是什么的？",
            'old_answer': "我是智能语音客服",
            'new_answer': "是的，我是美的官方智能客服，您可以放心咨询。"
        },
        {
            'question': "洗衣机维修多少钱？",
            'old_answer': "洗衣机和干衣机一般是提供上门维修的，特殊机型除外。报修后当地网点会主动联系您，到时候您可咨询维修费用相关事宜。",
            'new_answer': "洗衣机维修价格根据故障类型：简单故障80-120元，复杂故障150-200元，上门检测免费。请问您的洗衣机是什么故障？"
        }
    ]
    
    validator = AnswerValidator()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n案例 {i}")
        print("-" * 70)
        print(f"问题: {case['question']}")
        
        # 评估旧答案
        print(f"\n❌ 改进前:")
        print(f"   {case['old_answer']}")
        old_result = validator.validate(case['question'], case['old_answer'])
        print(f"   评分: {old_result.score:.2f} | 通过: {'✓' if old_result.is_valid else '✗'}")
        if not old_result.is_valid:
            print(f"   问题: {old_result.reason}")
        
        # 评估新答案
        print(f"\n✅ 改进后:")
        print(f"   {case['new_answer']}")
        new_result = validator.validate(case['question'], case['new_answer'])
        print(f"   评分: {new_result.score:.2f} | 通过: {'✓' if new_result.is_valid else '✗'}")


if __name__ == "__main__":
    # 运行完整演示
    demo()
    
    # 运行对比
    compare_old_vs_new()
    
    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("""
下一步建议：
1. 将 mock_llm_generate 替换为实际的4B模型调用
2. 扩充知识库（rag_system.py）添加更多FAQ
3. 收集badcase持续优化prompt和验证规则
4. 监控线上效果，调整验证阈值和重试策略
    """)
