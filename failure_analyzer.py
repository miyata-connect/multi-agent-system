# failure_analyzer.py
# 行数: 128行

from datetime import datetime, timedelta

class FailureAnalyzer:
    def __init__(self, tracker):
        self.tracker = tracker
    
    def get_top_failure_reasons(self, limit=5):
        cursor = self.tracker.conn.cursor()
        
        cursor.execute('''
            SELECT 
                error_type,
                COUNT(*) as occurrence_count,
                AVG(recovery_successful) as avg_recovery_rate,
                GROUP_CONCAT(DISTINCT agent_name) as affected_agents
            FROM agent_executions
            WHERE status = 'failed' AND error_type IS NOT NULL
            GROUP BY error_type
            ORDER BY occurrence_count DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'error_type': row['error_type'],
                'occurrence_count': row['occurrence_count'],
                'avg_recovery_rate': round(row['avg_recovery_rate'] * 100, 2) if row['avg_recovery_rate'] else 0,
                'affected_agents': row['affected_agents'].split(',') if row['affected_agents'] else []
            })
        
        return results
    
    def get_agent_performance(self):
        cursor = self.tracker.conn.cursor()
        
        cursor.execute('''
            SELECT 
                agent_name,
                role,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_tasks,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                AVG(token_used) as avg_tokens,
                SUM(cost_usd) as total_cost
            FROM agent_executions
            WHERE started_at >= datetime('now', '-7 days')
            GROUP BY agent_name, role
            ORDER BY total_tasks DESC
        ''')
        
        results = []
        for row in cursor.fetchall():
            total = row['total_tasks']
            success = row['successful_tasks']
            success_rate = (success / total * 100) if total > 0 else 0
            
            results.append({
                'agent_name': row['agent_name'],
                'role': row['role'],
                'total_tasks': total,
                'successful_tasks': success,
                'failed_tasks': row['failed_tasks'],
                'success_rate': round(success_rate, 2),
                'avg_tokens': round(row['avg_tokens']) if row['avg_tokens'] else 0,
                'total_cost': round(row['total_cost'], 4) if row['total_cost'] else 0
            })
        
        return results
    
    def analyze_time_based_patterns(self):
        cursor = self.tracker.conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%H', started_at) as hour,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures
            FROM agent_executions
            WHERE started_at >= datetime('now', '-7 days')
            GROUP BY hour
            ORDER BY failures DESC
            LIMIT 3
        ''')
        
        results = []
        for row in cursor.fetchall():
            total = row['total']
            failures = row['failures']
            failure_rate = (failures / total * 100) if total > 0 else 0
            
            results.append({
                'hour': f"{row['hour']}:00",
                'total_executions': total,
                'failures': failures,
                'failure_rate': round(failure_rate, 2)
            })
        
        return results
    
    def analyze_task_type_patterns(self):
        cursor = self.tracker.conn.cursor()
        
        cursor.execute('''
            SELECT 
                role,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures
            FROM agent_executions
            WHERE started_at >= datetime('now', '-7 days')
            GROUP BY role
            HAVING failures > 0
            ORDER BY failures DESC
        ''')
        
        results = []
        for row in cursor.fetchall():
            total = row['total']
            failures = row['failures']
            failure_rate = (failures / total * 100) if total > 0 else 0
            
            results.append({
                'role': row['role'],
                'total_tasks': total,
                'failures': failures,
                'failure_rate': round(failure_rate, 2)
            })
        
        return results
