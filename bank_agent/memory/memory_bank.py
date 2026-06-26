import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List

class MemoryBankManager:
    """Manages the stateful conversation memory bank using a local SQLite database.
    
    Provides isolated session storage for each customer (via customer_id) to ensure
    conversation history continuity. Only the Root Orchestrator is allowed to interact
    with this component.
    """
    
    def __init__(self, db_path: str = "memory_bank.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initializes the database schema if it doesn't already exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                customer_id TEXT PRIMARY KEY,
                history TEXT,
                summary TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def get_session_context(self, customer_id: str) -> Dict[str, Any]:
        """Retrieves previous conversation history and summary for a customer ID.
        
        Args:
            customer_id: The verified customer ID.
            
        Returns:
            A dictionary containing "history" (List of turns) and "summary" (str).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT history, summary FROM conversations WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                history = json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                history = []
            return {
                "history": history,
                "summary": row[1] or ""
            }
        
        return {
            "history": [],
            "summary": ""
        }
        
    def save_session_context(self, customer_id: str, history: List[Dict[str, Any]], summary: str = "") -> bool:
        """Saves or updates the conversation history and summary for a customer ID.
        
        Args:
            customer_id: The verified customer ID.
            history: List of dictionaries representing conversation turns.
            summary: Optional running summary of the conversation.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            history_json = json.dumps(history)
            updated_at = datetime.utcnow().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (customer_id, history, summary, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    history = excluded.history,
                    summary = excluded.summary,
                    updated_at = excluded.updated_at
            """, (customer_id, history_json, summary, updated_at))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to save context to Memory Bank: {str(e)}")
            return False

    def clear_session_context(self, customer_id: str) -> bool:
        """Clears/deletes the session context for a customer ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE customer_id = ?", (customer_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to clear context from Memory Bank: {str(e)}")
            return False
