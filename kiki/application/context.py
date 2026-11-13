"""Select bounded evidence for the local model independently of the UI."""
import re


def retrieve_context(memory, question):
    return [(identifier, text[:500], created)
            for identifier, text, created in memory.search(question)[:8]]


def unverified_citations(answer, records):
    """An ID being present is not proof of factual support; only flag absent IDs."""
    sent = {identifier for identifier, _, _ in records}
    cited = {int(bracket or hash_id) for bracket, hash_id in
             re.findall(r'\[(\d+)\]|(?<!\w)#(\d+)\b', answer)}
    return sorted(cited - sent)
