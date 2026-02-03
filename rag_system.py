"""
简化的RAG（检索增强生成）系统
用于从知识库检索相关信息，避免模型编造或模糊回答
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class KnowledgeItem:
    """知识库条目"""
    id: str
    category: str  # 类别：price, policy, product_info等
    question: str  # 标准问题
    answer: str  # 标准答案
    keywords: List[str]  # 关键词
    metadata: Dict = None  # 额外元数据


class SimpleKnowledgeBase:
    """简单的知识库实现（实际应用中应使用向量数据库）"""
    
    def __init__(self):
        self.items: List[KnowledgeItem] = []
        self._build_default_kb()
    
    def _build_default_kb(self):
        """构建默认知识库（示例数据）"""
        
        # 价格相关
        self.add_item(KnowledgeItem(
            id="price_washing_machine_repair",
            category="price",
            question="洗衣机维修多少钱？",
            answer="洗衣机维修价格根据故障类型：简单故障80-120元，复杂故障150-200元，上门检测免费。更换配件费用另计。",
            keywords=["洗衣机", "维修", "价格", "多少钱", "费用"]
        ))
        
        self.add_item(KnowledgeItem(
            id="price_ac_installation",
            category="price",
            question="空调安装多少钱？",
            answer="空调安装费用：挂机150元/台，柜机200元/台。如需额外配件（加长管、支架等）费用另计。",
            keywords=["空调", "安装", "价格", "多少钱", "费用"]
        ))
        
        self.add_item(KnowledgeItem(
            id="price_water_heater_installation",
            category="price",
            question="热水器安装多少钱？",
            answer="电热水器安装费用为每台410元。如需额外材料（阀门、软管等），费用在20-80元之间。",
            keywords=["热水器", "电热水器", "安装", "价格", "多少钱"]
        ))
        
        # 官方身份确认
        self.add_item(KnowledgeItem(
            id="identity_official",
            category="identity",
            question="你是官方客服吗？",
            answer="是的，我是美的官方智能客服，直接隶属于美的集团客户服务中心。您可以放心咨询任何问题。",
            keywords=["官方", "身份", "是不是", "客服"]
        ))
        
        # 保修政策
        self.add_item(KnowledgeItem(
            id="policy_warranty",
            category="policy",
            question="保修期是多久？",
            answer="美的产品保修政策：整机保修1年，主要部件保修3年。空调压缩机保修6年。保修期内非人为损坏免费维修。",
            keywords=["保修", "保修期", "多久", "质保"]
        ))
        
        self.add_item(KnowledgeItem(
            id="policy_warranty_coverage",
            category="policy",
            question="保修期内维修收费吗？",
            answer="保修期内如果是产品质量问题，维修完全免费，包括零件和人工费。但如果是人为损坏、私自拆卸或使用不当造成的故障，需要收费。",
            keywords=["保修", "收费", "免费", "质量问题"]
        ))
        
        # 服务时间
        self.add_item(KnowledgeItem(
            id="service_time",
            category="service",
            question="什么时候可以上门服务？",
            answer="上门服务时间：周一至周日 9:00-18:00，包括节假日。预约后通常24小时内上门。",
            keywords=["时间", "什么时候", "上门", "服务"]
        ))
    
    def add_item(self, item: KnowledgeItem):
        """添加知识库条目"""
        self.items.append(item)
    
    def search(
        self, 
        query: str, 
        top_k: int = 3,
        category: Optional[str] = None
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        搜索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回top k结果
            category: 限定类别
            
        Returns:
            [(KnowledgeItem, score), ...] 按相关性排序
        """
        results = []
        
        for item in self.items:
            # 类别过滤
            if category and item.category != category:
                continue
            
            # 计算相关性分数（简单的关键词匹配）
            score = self._calculate_relevance(query, item)
            
            if score > 0:
                results.append((item, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _calculate_relevance(self, query: str, item: KnowledgeItem) -> float:
        """计算相关性分数（简化版本）"""
        score = 0.0
        
        # 关键词匹配
        for keyword in item.keywords:
            if keyword in query:
                score += 1.0
        
        # 问题相似度（简单字符重叠）
        query_chars = set(query)
        question_chars = set(item.question)
        overlap = len(query_chars & question_chars)
        score += overlap * 0.1
        
        return score
    
    def get_by_category(self, category: str) -> List[KnowledgeItem]:
        """获取某个类别的所有知识"""
        return [item for item in self.items if item.category == category]
    
    def load_from_json(self, filepath: str):
        """从JSON文件加载知识库"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item_data in data:
                item = KnowledgeItem(**item_data)
                self.add_item(item)
    
    def save_to_json(self, filepath: str):
        """保存知识库到JSON文件"""
        data = []
        for item in self.items:
            data.append({
                'id': item.id,
                'category': item.category,
                'question': item.question,
                'answer': item.answer,
                'keywords': item.keywords,
                'metadata': item.metadata
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class IntentClassifier:
    """意图分类器 - 识别用户意图以便检索对应知识"""
    
    def __init__(self):
        # 意图识别规则（实际应用中应使用模型）
        self.intent_patterns = {
            'price_inquiry': [
                r'多少钱', r'价格', r'费用', r'收费', r'怎么.*收.*费'
            ],
            'identity_confirmation': [
                r'官方', r'是不是.*的', r'你是谁', r'什么.*客服'
            ],
            'warranty_inquiry': [
                r'保修', r'质保', r'保修期', r'保多久'
            ],
            'appointment': [
                r'预约', r'什么时候.*上门', r'能.*来', r'安排'
            ],
            'complaint': [
                r'投诉', r'问题', r'不满意', r'质量.*差'
            ]
        }
        
        # 意图到知识库类别的映射
        self.intent_to_category = {
            'price_inquiry': 'price',
            'identity_confirmation': 'identity',
            'warranty_inquiry': 'policy',
            'appointment': 'service'
        }
    
    def classify(self, text: str) -> Optional[str]:
        """分类用户意图"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return intent
        return None
    
    def get_category(self, intent: str) -> Optional[str]:
        """根据意图获取知识库类别"""
        return self.intent_to_category.get(intent)


class RAGSystem:
    """RAG系统 - 整合意图识别和知识检索"""
    
    def __init__(self, knowledge_base: SimpleKnowledgeBase = None):
        self.kb = knowledge_base or SimpleKnowledgeBase()
        self.intent_classifier = IntentClassifier()
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 2
    ) -> Dict:
        """
        检索相关知识
        
        Args:
            query: 用户查询
            top_k: 返回数量
            
        Returns:
            {
                'intent': str,
                'knowledge': [KnowledgeItem, ...],
                'context_text': str  # 用于注入prompt的文本
            }
        """
        # 1. 意图识别
        intent = self.intent_classifier.classify(query)
        
        # 2. 知识检索
        category = self.intent_classifier.get_category(intent) if intent else None
        results = self.kb.search(query, top_k=top_k, category=category)
        
        # 3. 构建上下文文本
        knowledge_items = [item for item, score in results]
        context_text = self._build_context_text(knowledge_items)
        
        return {
            'intent': intent,
            'knowledge': knowledge_items,
            'context_text': context_text
        }
    
    def _build_context_text(self, items: List[KnowledgeItem]) -> str:
        """构建用于注入prompt的上下文文本"""
        if not items:
            return ""
        
        context_parts = ["以下是相关的知识库信息，请基于这些信息回答用户问题：\n"]
        
        for i, item in enumerate(items, 1):
            context_parts.append(f"{i}. 【{item.category}】{item.question}")
            context_parts.append(f"   {item.answer}\n")
        
        return "\n".join(context_parts)
    
    def answer_with_rag(
        self, 
        query: str,
        llm_generate_func,  # LLM生成函数
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        使用RAG生成答案
        
        Args:
            query: 用户问题
            llm_generate_func: LLM生成函数，接收prompt返回答案
            conversation_history: 对话历史
            
        Returns:
            {
                'answer': str,
                'intent': str,
                'knowledge_used': [KnowledgeItem, ...]
            }
        """
        # 1. 检索相关知识
        retrieval_result = self.retrieve(query)
        
        # 2. 构建增强prompt
        from enhanced_prompts import CustomerServicePrompts
        prompts = CustomerServicePrompts()
        
        enhanced_prompt = prompts.build_prompt_with_context(
            user_question=query,
            conversation_history=conversation_history,
            knowledge_context=retrieval_result['context_text'],
            use_few_shot=True
        )
        
        # 3. 生成答案
        answer = llm_generate_func(enhanced_prompt)
        
        return {
            'answer': answer,
            'intent': retrieval_result['intent'],
            'knowledge_used': retrieval_result['knowledge']
        }


# 使用示例
if __name__ == "__main__":
    # 初始化RAG系统
    rag = RAGSystem()
    
    print("=" * 60)
    print("RAG系统测试")
    print("=" * 60)
    
    # 测试1：价格咨询
    print("\n测试1: 价格咨询")
    print("-" * 60)
    query1 = "洗衣机维修大概多少钱？"
    result1 = rag.retrieve(query1)
    
    print(f"问题: {query1}")
    print(f"识别意图: {result1['intent']}")
    print(f"检索到的知识: {len(result1['knowledge'])}条")
    print(f"\n上下文文本:\n{result1['context_text']}")
    
    # 测试2：身份确认
    print("\n测试2: 身份确认")
    print("-" * 60)
    query2 = "你是官方的客服吗？"
    result2 = rag.retrieve(query2)
    
    print(f"问题: {query2}")
    print(f"识别意图: {result2['intent']}")
    print(f"检索到的知识: {len(result2['knowledge'])}条")
    print(f"\n上下文文本:\n{result2['context_text']}")
    
    # 测试3：保修咨询
    print("\n测试3: 保修咨询")
    print("-" * 60)
    query3 = "保修期内修理要钱吗？"
    result3 = rag.retrieve(query3)
    
    print(f"问题: {query3}")
    print(f"识别意图: {result3['intent']}")
    print(f"检索到的知识: {len(result3['knowledge'])}条")
    print(f"\n上下文文本:\n{result3['context_text']}")
    
    # 测试知识库导出
    print("\n" + "=" * 60)
    print("知识库导出测试")
    print("=" * 60)
    
    kb = SimpleKnowledgeBase()
    kb.save_to_json('/tmp/knowledge_base.json')
    print("知识库已保存到: /tmp/knowledge_base.json")
    
    # 显示知识库统计
    categories = {}
    for item in kb.items:
        categories[item.category] = categories.get(item.category, 0) + 1
    
    print(f"\n知识库统计:")
    print(f"总条目数: {len(kb.items)}")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}条")
