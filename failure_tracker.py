# failure_tracker.py
# 行数: 145行

import sqlite3
import os
from datetime import datetime
from pathlib import Path

class FailureTracker:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = Path(__file__).parent
            data_dir = base_dir / 'data'
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / 'failures.db'
        
        self.db_path = str(db_path)
        self.conn = None
        self.initialize()
    
    def initialize(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        print('✓ Failure Tracker初期化完了')
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                agent_name TEXT NOT NULL,
                role TEXT NOT NULL,
                task_description TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                status TEXT NOT NULL,
                error_message TEXT,
                error_type TEXT,
                recovery_attempted BOOLEAN DEFAULT 0,
                recovery_successful BOOLEAN DEFAULT 0,
                token_used INTEGER,
                cost_usd REAL,
                user_visible BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failure_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                auto_recoverable BOOLEAN DEFAULT 0,
                FOREIGN KEY (execution_id) REFERENCES agent_executions(execution_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                failure_category TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                implemented_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                effectiveness_score REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_acquisitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                failure_type TEXT NOT NULL,
                role_id TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                skill_source TEXT,
                priority REAL,
                acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_status ON agent_executions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_date ON agent_executions(started_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_name ON agent_executions(agent_name)')
        
        self.conn.commit()
    
    def record_execution(self, execution_id, agent_name, role, task_description, 
                        status, error_message=None, error_type=None, 
                        token_used=0, cost_usd=0):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_executions 
            (execution_id, agent_name, role, task_description, status, 
             error_message, error_type, token_used, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (execution_id, agent_name, role, task_description, status,
              error_message, error_type, token_used, cost_usd))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_execution(self, execution_id, completed_at=None, status=None,
                        error_message=None, error_type=None,
                        recovery_attempted=False, recovery_successful=False):
        if completed_at is None:
            completed_at = datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE agent_executions 
            SET completed_at = ?, status = ?, error_message = ?, error_type = ?,
                recovery_attempted = ?, recovery_successful = ?
            WHERE execution_id = ?
        ''', (completed_at, status, error_message, error_type,
              1 if recovery_attempted else 0,
              1 if recovery_successful else 0,
              execution_id))
        
        self.conn.commit()
        return cursor.rowcount
    
    def categorize_failure(self, execution_id, category, severity, auto_recoverable=False):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO failure_categories (execution_id, category, severity, auto_recoverable)
            VALUES (?, ?, ?, ?)
        ''', (execution_id, category, severity, 1 if auto_recoverable else 0))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_failure_rate(self, period_hours=24):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN recovery_attempted = 1 THEN 1 ELSE 0 END) as recovery_attempts,
                SUM(CASE WHEN recovery_successful = 1 THEN 1 ELSE 0 END) as successful_recoveries
            FROM agent_executions
            WHERE started_at >= datetime('now', '-' || ? || ' hours')
        ''', (period_hours,))
        
        row = cursor.fetchone()
        
        total = row['total_executions'] or 0
        failed = row['failed_executions'] or 0
        success = row['successful_executions'] or 0
        recovery_attempts = row['recovery_attempts'] or 0
        successful_recoveries = row['successful_recoveries'] or 0
        
        failure_rate = (failed / total * 100) if total > 0 else 0
        recovery_rate = (successful_recoveries / recovery_attempts * 100) if recovery_attempts > 0 else 0
        
        return {
            'total_executions': total,
            'failed_executions': failed,
            'successful_executions': success,
            'failure_rate': round(failure_rate, 2),
            'recovery_attempts': recovery_attempts,
            'successful_recoveries': successful_recoveries,
            'recovery_success_rate': round(recovery_rate, 2)
        }
    
    def close(self):
        if self.conn:
            self.conn.close()
