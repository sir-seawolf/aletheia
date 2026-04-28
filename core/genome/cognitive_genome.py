class CognitiveGenome:

    def __init__(self):
        self.genes = []

    def encode(self, experience: dict):

        gene = {
            "context_type": experience.get("domain"),
            "complexity_pattern": experience.get("complexity"),
            "architecture_used": experience.get("architecture_state"),
            "efficiency_score": experience.get("efficiency"),
            "decision_path": experience.get("path"),
        }

        self.genes.append(gene)

        return gene

    def search_genome(self, context_type, complexity):

        return [
            gene for gene in self.genes
            if gene["context_type"] == context_type
            and gene["complexity_pattern"] == complexity
        ]

