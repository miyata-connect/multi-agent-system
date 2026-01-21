# team_evaluator.py
# エージェントチーム入れ替え評価システム
# B(履歴ベース) + C(ベンチマーク) + A(A/Bテスト)

import sqlite3
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# データベース初期化
# ==========================================
DB_PATH = "data/team_evaluations.db"

def init_db():
    """データベース初期化"""
    import os
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # チーム評価履歴テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_key TEXT NOT NULL,
            team_config TEXT NOT NULL,
            task_type TEXT NOT NULL,
            task_hash TEXT NOT NULL,
            quality_score REAL,
            response_time REAL,
            token_count INTEGER,
            success INTEGER DEFAULT 1,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ベンチマーク結果テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benchmark_id TEXT NOT NULL,
            team_key TEXT NOT NULL,
            team_config TEXT NOT NULL,
            benchmark_name TEXT NOT NULL,
            score REAL,
            response_time REAL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # A/Bテスト結果テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ab_test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT NOT NULL,
            task TEXT NOT NULL,
            team_a_config TEXT NOT NULL,
            team_a_result TEXT,
            team_a_score REAL,
            team_a_time REAL,
            team_b_config TEXT NOT NULL,
            team_b_result TEXT,
            team_b_score REAL,
            team_b_time REAL,
            winner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# 初期化実行
init_db()


# ==========================================
# チーム構成ハッシュ生成
# ==========================================
def get_team_config_hash(team_config: Dict) -> str:
    """チーム構成のハッシュを生成"""
    config_str = json.dumps(team_config, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:8]


def get_task_hash(task: str) -> str:
    """タスクのハッシュを生成（類似タスク検索用）"""
    # 簡易的なハッシュ（実際はより高度な類似度計算が望ましい）
    normalized = task.lower().strip()[:100]
    return hashlib.md5(normalized.encode()).hexdigest()[:8]


# ==========================================
# B方式: 履歴ベース評価
# ==========================================
class HistoryBasedEvaluator:
    """履歴ベースの評価システム"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def record_execution(
        self,
        team_key: str,
        team_config: Dict,
        task_type: str,
        task: str,
        quality_score: Optional[float] = None,
        response_time: Optional[float] = None,
        token_count: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """実行結果を記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO team_evaluations 
            (team_key, team_config, task_type, task_hash, quality_score, 
             response_time, token_count, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            team_key,
            json.dumps(team_config),
            task_type,
            get_task_hash(task),
            quality_score,
            response_time,
            token_count,
            1 if success else 0,
            error_message
        ))
        
        conn.commit()
        conn.close()
    
    def get_team_stats(self, team_key: str, days: int = 30) -> Dict:
        """チームの統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(quality_score) as avg_score,
                AVG(response_time) as avg_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                AVG(token_count) as avg_tokens
            FROM team_evaluations
            WHERE team_key = ? AND created_at >= ?
        ''', (team_key, since.isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            return {
                "total_executions": row[0],
                "avg_quality_score": round(row[1], 1) if row[1] else None,
                "avg_response_time": round(row[2], 2) if row[2] else None,
                "success_rate": round(row[3] / row[0] * 100, 1) if row[0] > 0 else 0,
                "avg_tokens": int(row[4]) if row[4] else None
            }
        return {
            "total_executions": 0,
            "avg_quality_score": None,
            "avg_response_time": None,
            "success_rate": 0,
            "avg_tokens": None
        }
    
    def get_all_teams_comparison(self, days: int = 30) -> List[Dict]:
        """全チームの比較データを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT 
                team_key,
                team_config,
                COUNT(*) as total,
                AVG(quality_score) as avg_score,
                AVG(response_time) as avg_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM team_evaluations
            WHERE created_at >= ?
            GROUP BY team_key
            ORDER BY avg_score DESC
        ''', (since.isoformat(),))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "team_key": row[0],
                "team_config": json.loads(row[1]) if row[1] else {},
                "total_executions": row[2],
                "avg_quality_score": round(row[3], 1) if row[3] else None,
                "avg_response_time": round(row[4], 2) if row[4] else None,
                "success_rate": round(row[5], 1) if row[5] else 0
            })
        
        conn.close()
        return results
    
    def get_best_team_for_task_type(self, task_type: str) -> Optional[Dict]:
        """タスクタイプに最適なチームを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                team_key,
                team_config,
                AVG(quality_score) as avg_score,
                COUNT(*) as count
            FROM team_evaluations
            WHERE task_type = ? AND quality_score IS NOT NULL
            GROUP BY team_key
            HAVING count >= 3
            ORDER BY avg_score DESC
            LIMIT 1
        ''', (task_type,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "team_key": row[0],
                "team_config": json.loads(row[1]) if row[1] else {},
                "avg_score": round(row[2], 1),
                "sample_count": row[3]
            }
        return None


# ==========================================
# C方式: ベンチマーク評価
# ==========================================
class BenchmarkEvaluator:
    """ベンチマークテスト評価システム"""
    
    # 標準ベンチマークタスク
    BENCHMARK_TASKS = {
        "coder": [
            {
                "name": "フィボナッチ関数",
                "task": "Pythonでフィボナッチ数列のn番目を計算する関数を作成してください。",
                "expected_keywords": ["def", "fibonacci", "return"]
            },
            {
                "name": "リスト操作",
                "task": "Pythonでリストの重複を削除して昇順ソートする関数を作成してください。",
                "expected_keywords": ["def", "list", "sort", "set"]
            },
            {
                "name": "API呼び出し",
                "task": "Pythonでrequestsを使ってJSONデータを取得する関数を作成してください。",
                "expected_keywords": ["requests", "json", "get"]
            }
        ],
        "auditor": [
            {
                "name": "コードレビュー",
                "task": "以下のコードの問題点を指摘してください:\ndef add(a,b): return a+b\nresult = add('1', 2)",
                "expected_keywords": ["型", "エラー", "TypeError"]
            }
        ],
        "data": [
            {
                "name": "データ分析",
                "task": "売上データ [100, 150, 200, 180, 220] の平均、最大、最小、傾向を分析してください。",
                "expected_keywords": ["平均", "最大", "最小", "傾向"]
            }
        ],
        "searcher": [
            {
                "name": "情報検索",
                "task": "Pythonの非同期処理について簡潔に説明してください。",
                "expected_keywords": ["async", "await", "非同期"]
            }
        ]
    }
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def run_benchmark(
        self,
        team_key: str,
        team_config: Dict,
        team_runner,  # チーム実行関数
        benchmark_id: Optional[str] = None
    ) -> Dict:
        """ベンチマークテストを実行"""
        import uuid
        
        if benchmark_id is None:
            benchmark_id = str(uuid.uuid4())[:8]
        
        tasks = self.BENCHMARK_TASKS.get(team_key, [])
        if not tasks:
            return {"error": f"ベンチマークタスクが定義されていません: {team_key}"}
        
        results = []
        total_score = 0
        total_time = 0
        
        for task_info in tasks:
            start_time = time.time()
            
            try:
                # チーム実行
                result = team_runner(task_info["task"])
                elapsed = time.time() - start_time
                
                # スコア計算（キーワードマッチング）
                result_lower = result.lower() if result else ""
                matched = sum(1 for kw in task_info["expected_keywords"] if kw.lower() in result_lower)
                score = (matched / len(task_info["expected_keywords"])) * 100
                
                results.append({
                    "name": task_info["name"],
                    "score": round(score, 1),
                    "time": round(elapsed, 2),
                    "success": True
                })
                
                total_score += score
                total_time += elapsed
                
            except Exception as e:
                results.append({
                    "name": task_info["name"],
                    "score": 0,
                    "time": 0,
                    "success": False,
                    "error": str(e)
                })
        
        # 結果を保存
        avg_score = total_score / len(tasks) if tasks else 0
        avg_time = total_time / len(tasks) if tasks else 0
        
        self._save_benchmark_result(
            benchmark_id=benchmark_id,
            team_key=team_key,
            team_config=team_config,
            benchmark_name=f"{team_key}_standard",
            score=avg_score,
            response_time=avg_time,
            details=results
        )
        
        return {
            "benchmark_id": benchmark_id,
            "team_key": team_key,
            "avg_score": round(avg_score, 1),
            "avg_time": round(avg_time, 2),
            "task_results": results
        }
    
    def _save_benchmark_result(
        self,
        benchmark_id: str,
        team_key: str,
        team_config: Dict,
        benchmark_name: str,
        score: float,
        response_time: float,
        details: List[Dict]
    ):
        """ベンチマーク結果を保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO benchmark_results 
            (benchmark_id, team_key, team_config, benchmark_name, score, response_time, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            benchmark_id,
            team_key,
            json.dumps(team_config),
            benchmark_name,
            score,
            response_time,
            json.dumps(details)
        ))
        
        conn.commit()
        conn.close()
    
    def get_benchmark_history(self, team_key: str, limit: int = 10) -> List[Dict]:
        """ベンチマーク履歴を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT benchmark_id, team_config, score, response_time, details, created_at
            FROM benchmark_results
            WHERE team_key = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (team_key, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "benchmark_id": row[0],
                "team_config": json.loads(row[1]) if row[1] else {},
                "score": row[2],
                "response_time": row[3],
                "details": json.loads(row[4]) if row[4] else [],
                "created_at": row[5]
            })
        
        conn.close()
        return results


# ==========================================
# A方式: A/Bテスト
# ==========================================
class ABTestEvaluator:
    """A/Bテスト評価システム"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def run_ab_test(
        self,
        task: str,
        team_a_config: Dict,
        team_b_config: Dict,
        team_a_runner,  # チームA実行関数
        team_b_runner,  # チームB実行関数
        cross_checker=None  # クロスチェック関数（オプション）
    ) -> Dict:
        """A/Bテストを実行"""
        import uuid
        
        test_id = str(uuid.uuid4())[:8]
        results = {"team_a": None, "team_b": None}
        
        # 並列実行
        def run_team(name, runner, config):
            start = time.time()
            try:
                result = runner(task)
                elapsed = time.time() - start
                return {
                    "name": name,
                    "config": config,
                    "result": result,
                    "time": elapsed,
                    "success": True,
                    "score": None
                }
            except Exception as e:
                return {
                    "name": name,
                    "config": config,
                    "result": str(e),
                    "time": time.time() - start,
                    "success": False,
                    "score": 0
                }
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(run_team, "team_a", team_a_runner, team_a_config)
            future_b = executor.submit(run_team, "team_b", team_b_runner, team_b_config)
            
            results["team_a"] = future_a.result()
            results["team_b"] = future_b.result()
        
        # クロスチェックでスコア付け（オプション）
        if cross_checker and results["team_a"]["success"] and results["team_b"]["success"]:
            try:
                score_a = cross_checker(results["team_a"]["result"], task)
                score_b = cross_checker(results["team_b"]["result"], task)
                results["team_a"]["score"] = score_a
                results["team_b"]["score"] = score_b
            except:
                pass
        
        # 勝者判定
        winner = self._determine_winner(results["team_a"], results["team_b"])
        
        # 結果を保存
        self._save_ab_test_result(test_id, task, results, winner)
        
        return {
            "test_id": test_id,
            "task": task[:100],
            "team_a": results["team_a"],
            "team_b": results["team_b"],
            "winner": winner
        }
    
    def _determine_winner(self, team_a: Dict, team_b: Dict) -> str:
        """勝者を判定"""
        # 成功/失敗
        if team_a["success"] and not team_b["success"]:
            return "team_a"
        if team_b["success"] and not team_a["success"]:
            return "team_b"
        if not team_a["success"] and not team_b["success"]:
            return "draw"
        
        # スコアがある場合
        if team_a.get("score") is not None and team_b.get("score") is not None:
            if team_a["score"] > team_b["score"] + 5:  # 5点以上差
                return "team_a"
            elif team_b["score"] > team_a["score"] + 5:
                return "team_b"
        
        # 速度で判定
        if team_a["time"] < team_b["time"] * 0.8:  # 20%以上速い
            return "team_a"
        elif team_b["time"] < team_a["time"] * 0.8:
            return "team_b"
        
        return "draw"
    
    def _save_ab_test_result(self, test_id: str, task: str, results: Dict, winner: str):
        """A/Bテスト結果を保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ab_test_results 
            (test_id, task, team_a_config, team_a_result, team_a_score, team_a_time,
             team_b_config, team_b_result, team_b_score, team_b_time, winner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_id,
            task[:500],
            json.dumps(results["team_a"]["config"]),
            results["team_a"]["result"][:2000] if results["team_a"]["result"] else None,
            results["team_a"].get("score"),
            results["team_a"]["time"],
            json.dumps(results["team_b"]["config"]),
            results["team_b"]["result"][:2000] if results["team_b"]["result"] else None,
            results["team_b"].get("score"),
            results["team_b"]["time"],
            winner
        ))
        
        conn.commit()
        conn.close()
    
    def get_ab_test_history(self, limit: int = 10) -> List[Dict]:
        """A/Bテスト履歴を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_id, task, team_a_config, team_a_score, team_a_time,
                   team_b_config, team_b_score, team_b_time, winner, created_at
            FROM ab_test_results
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "test_id": row[0],
                "task": row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                "team_a": {
                    "config": json.loads(row[2]) if row[2] else {},
                    "score": row[3],
                    "time": row[4]
                },
                "team_b": {
                    "config": json.loads(row[5]) if row[5] else {},
                    "score": row[6],
                    "time": row[7]
                },
                "winner": row[8],
                "created_at": row[9]
            })
        
        conn.close()
        return results


# ==========================================
# 統合評価マネージャー
# ==========================================
class TeamEvaluationManager:
    """チーム評価の統合マネージャー"""
    
    def __init__(self):
        self.history_evaluator = HistoryBasedEvaluator()
        self.benchmark_evaluator = BenchmarkEvaluator()
        self.ab_test_evaluator = ABTestEvaluator()
    
    def record_execution(self, **kwargs):
        """実行結果を記録（B方式）"""
        return self.history_evaluator.record_execution(**kwargs)
    
    def get_team_stats(self, team_key: str, days: int = 30) -> Dict:
        """チーム統計を取得（B方式）"""
        return self.history_evaluator.get_team_stats(team_key, days)
    
    def get_all_teams_comparison(self, days: int = 30) -> List[Dict]:
        """全チーム比較（B方式）"""
        return self.history_evaluator.get_all_teams_comparison(days)
    
    def get_best_team_for_task(self, task_type: str) -> Optional[Dict]:
        """タスクに最適なチーム（B方式）"""
        return self.history_evaluator.get_best_team_for_task_type(task_type)
    
    def run_benchmark(self, team_key: str, team_config: Dict, team_runner) -> Dict:
        """ベンチマーク実行（C方式）"""
        return self.benchmark_evaluator.run_benchmark(team_key, team_config, team_runner)
    
    def get_benchmark_history(self, team_key: str, limit: int = 10) -> List[Dict]:
        """ベンチマーク履歴（C方式）"""
        return self.benchmark_evaluator.get_benchmark_history(team_key, limit)
    
    def run_ab_test(self, task: str, team_a_config: Dict, team_b_config: Dict,
                    team_a_runner, team_b_runner, cross_checker=None) -> Dict:
        """A/Bテスト実行（A方式）"""
        return self.ab_test_evaluator.run_ab_test(
            task, team_a_config, team_b_config,
            team_a_runner, team_b_runner, cross_checker
        )
    
    def get_ab_test_history(self, limit: int = 10) -> List[Dict]:
        """A/Bテスト履歴（A方式）"""
        return self.ab_test_evaluator.get_ab_test_history(limit)
    
    def get_recommendation(self, task_type: str) -> Dict:
        """チーム構成の推奨を取得"""
        # 履歴ベースの最適チーム
        best_history = self.history_evaluator.get_best_team_for_task_type(task_type)
        
        # 最新のベンチマーク結果
        benchmark_history = self.benchmark_evaluator.get_benchmark_history(task_type, limit=5)
        
        # A/Bテストの勝率
        ab_history = self.ab_test_evaluator.get_ab_test_history(limit=20)
        
        return {
            "task_type": task_type,
            "best_from_history": best_history,
            "recent_benchmarks": benchmark_history[:3] if benchmark_history else [],
            "ab_test_insights": self._analyze_ab_tests(ab_history)
        }
    
    def _analyze_ab_tests(self, ab_history: List[Dict]) -> Dict:
        """A/Bテスト結果を分析"""
        if not ab_history:
            return {"message": "A/Bテスト履歴なし"}
        
        wins = {"team_a": 0, "team_b": 0, "draw": 0}
        for test in ab_history:
            wins[test["winner"]] = wins.get(test["winner"], 0) + 1
        
        return {
            "total_tests": len(ab_history),
            "win_distribution": wins
        }


# シングルトンインスタンス
_manager = None

def get_evaluation_manager() -> TeamEvaluationManager:
    """評価マネージャーのシングルトンを取得"""
    global _manager
    if _manager is None:
        _manager = TeamEvaluationManager()
    return _manager
