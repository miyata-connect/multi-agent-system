# learning_integrator.py
# 行数: 98行

from datetime import datetime

class LearningSkillsIntegrator:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.skill_map = {
            'rate_limit_exceeded': [
                {'name': 'Rate Limiter Pro', 'category': 'resilience', 'priority': 'high'},
                {'name': 'Backoff Strategy', 'category': 'retry-logic', 'priority': 'high'},
                {'name': 'Queue Manager', 'category': 'optimization', 'priority': 'medium'}
            ],
            'timeout': [
                {'name': 'Timeout Handler', 'category': 'error-handling', 'priority': 'high'},
                {'name': 'Circuit Breaker', 'category': 'resilience', 'priority': 'high'},
                {'name': 'Async Retry Logic', 'category': 'retry-logic', 'priority': 'medium'}
            ],
            'invalid_response': [
                {'name': 'Response Validator', 'category': 'validation', 'priority': 'high'},
                {'name': 'Schema Checker', 'category': 'validation', 'priority': 'medium'},
                {'name': 'Data Sanitizer', 'category': 'security', 'priority': 'medium'}
            ],
            'authentication_failed': [
                {'name': 'Auth Refresher', 'category': 'authentication', 'priority': 'critical'},
                {'name': 'Token Manager', 'category': 'authentication', 'priority': 'high'}
            ],
            'api_error': [
                {'name': 'API Error Handler', 'category': 'error-handling', 'priority': 'high'},
                {'name': 'Fallback Strategy', 'category': 'resilience', 'priority': 'medium'}
            ]
        }
    
    def generate_skill_recommendations(self, failure):
        error_type = failure['error_type']
        skills = self.skill_map.get(error_type, [
            {'name': 'Generic Error Handler', 'category': 'error-handling', 'priority': 'low'}
        ])
        
        return [{
            **skill,
            'failure_context': error_type,
            'affected_agents': failure.get('affected_agents', [])
        } for skill in skills]
    
    def calculate_priority(self, failure):
        frequency_score = min(failure['occurrence_count'] / 10, 10)
        recovery_score = (100 - failure['avg_recovery_rate']) / 10
        return frequency_score + recovery_score
    
    def analyze_failures_and_learn(self):
        print('\n=== 失敗分析 & 学習プロセス開始 ===\n')
        
        top_failures = self.analyzer.get_top_failure_reasons(10)
        print(f'検出された失敗パターン: {len(top_failures)}件\n')
        
        learning_actions = []
        
        for failure in top_failures:
            print(f"[失敗分析] {failure['error_type']}")
            print(f"  発生回数: {failure['occurrence_count']}回")
            print(f"  現在のリカバリー率: {failure['avg_recovery_rate']}%")
            
            recommended_skills = self.generate_skill_recommendations(failure)
            
            if recommended_skills:
                print(f"  → {len(recommended_skills)}個の対応Skillsを推薦")
                
                learning_actions.append({
                    'failure_type': failure['error_type'],
                    'recommended_skills': recommended_skills,
                    'priority': self.calculate_priority(failure),
                    'timestamp': datetime.now().isoformat()
                })
            
            print('')
        
        learning_actions.sort(key=lambda x: x['priority'], reverse=True)
        
        print(f"\n優先度順に{len(learning_actions)}件の学習推薦を生成しました\n")
        print('=== 学習プロセス完了 ===\n')
        
        return learning_actions
    
    def generate_learning_report(self):
        top_failures = self.analyzer.get_top_failure_reasons(5)
        
        report_lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║              学習型Skills推薦レポート                       ║",
            "╚════════════════════════════════════════════════════════════╝",
            ""
        ]
        
        for i, failure in enumerate(top_failures, 1):
            skills = self.generate_skill_recommendations(failure)
            skill_names = [s['name'] for s in skills[:3]]
            
            report_lines.extend([
                f"{i}. [{failure['error_type']}]",
                f"   発生回数: {failure['occurrence_count']}回",
                f"   現在のリカバリー率: {failure['avg_recovery_rate']}%",
                "   ",
                "   推薦Skills:"
            ])
            
            for skill_name in skill_names:
                report_lines.append(f"   - {skill_name}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
