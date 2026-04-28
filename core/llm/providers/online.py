class OnlineProvider:
    def __init__(self):
        raise NotImplementedError("Online providers coming in future versions.")

    def generate(self, prompt: str, temp: float = 0.3, model: str = None) -> str:
        raise NotImplementedError("Online providers not implemented yet.")

