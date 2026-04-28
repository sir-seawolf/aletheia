class CognitiveEconomy:

    def __init__(self):
        self.total = 100
        self.available = 100
        self.regen_rate = 5

    def can_afford(self, cost: int) -> bool:
        return self.available >= cost

    def spend(self, cost: int):
        self.available = max(0, self.available - cost)

    def regenerate(self):
        self.available = min(self.total, self.available + self.regen_rate)

    def status(self):
        return {
            "available": self.available,
            "total": self.total,
            "pressure": 1 - (self.available / self.total)
        }

