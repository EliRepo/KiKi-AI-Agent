"""Select bounded evidence for the local model independently of the UI."""


def retrieve_context(memory, question):
    return [(identifier, text[:500], created)
            for identifier, text, created in memory.search(question)[:8]]
