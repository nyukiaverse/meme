from dataclasses import dataclass
from typing import Set
from datetime import datetime

@dataclass
class BotStats:
    total_memes: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    unique_users: Set[int] = None
    
    def __post_init__(self):
        if self.unique_users is None:
            self.unique_users = set()

    def track_usage(self, user_id: int, success: bool):
        """Track bot usage statistics"""
        self.total_memes += 1
        self.unique_users.add(user_id)
        if success:
            self.successful_generations += 1
        else:
            self.failed_generations += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_memes == 0:
            return 0.0
        return (self.successful_generations / self.total_memes) * 100

stats = BotStats() 