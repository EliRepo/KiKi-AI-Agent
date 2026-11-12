import datetime as dt
import re
from .text import normalize

def parse_reminder(text, now=None):
    """Accept a small, explicit vocabulary; never guess a missing time."""
    now = now or dt.datetime.now()
    clean = normalize(text)
    day = re.search(r'\b(hoje|amanha|\d{2}/\d{2}/\d{4})\b', clean)
    time = re.search(r'\b(?:as\s+)(\d{1,2})(?::(\d{2})|h(\d{2})?)?\b', clean)
    if not day or not time:
        raise ValueError('Informe hoje, amanhã ou DD/MM/AAAA e um horário, como “amanhã às 10h”.')
    if day[1] in ('hoje', 'amanha'):
        date = now.date() + dt.timedelta(days=int(day[1] == 'amanha'))
    else:
        date = dt.datetime.strptime(day[1], '%d/%m/%Y').date()
    due = dt.datetime.combine(date, dt.time(int(time[1]), int(time[2] or time[3] or 0)))
    if due <= now:
        raise ValueError('Esse horário já passou. Informe uma data e hora futuras.')
    return due


