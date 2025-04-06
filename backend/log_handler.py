import logging
import time
from collections import deque
import threading
import queue

class MemoryLogHandler(logging.Handler):
    """
    A logging handler that keeps logs in memory with a maximum capacity
    """
    def __init__(self, capacity=1000):
        """
        Initialize the handler with a maximum capacity
        
        Args:
            capacity: Maximum number of log entries to keep
        """
        super().__init__()
        self.logs = deque(maxlen=capacity)
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.running = True
        
        # Start a worker thread to process log records
        self.worker = threading.Thread(target=self._process_logs)
        self.worker.daemon = True
        self.worker.start()
        
    def _process_logs(self):
        """Process log records from the queue"""
        while self.running:
            try:
                record = self.queue.get(timeout=0.5)
                with self.lock:
                    self.logs.appendleft(record)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                continue
    
    def emit(self, record):
        """
        Add a log record to the memory buffer
        
        Args:
            record: Log record to add
        """
        if not self.running:
            return
            
        try:
            # Format the message
            message = self.format(record)
            
            # Create log entry
            log_entry = {
                'timestamp': time.time(),
                'level': record.levelname,
                'message': message,
                'source': record.name
            }
            
            # Add to queue for processing
            self.queue.put(log_entry)
        except Exception:
            pass
    
    def get_logs(self, limit=100, level=None):
        """
        Get logs from the memory buffer
        
        Args:
            limit: Maximum number of logs to return
            level: Filter logs by level (e.g., 'INFO', 'ERROR')
            
        Returns:
            list: List of log entries
        """
        with self.lock:
            if level:
                filtered_logs = [log for log in self.logs if log['level'] == level]
                return list(filtered_logs)[-limit:]
            return list(self.logs)[-limit:]
            
    def close(self):
        """Close the handler and stop the worker thread"""
        self.running = False
        if self.worker.is_alive():
            self.worker.join(timeout=1.0)
        super().close()