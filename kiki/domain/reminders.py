import datetime as dt
import re
from dataclasses import dataclass
from .text import normalize


class ReminderNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class Reminder:
    id: int
    text: str
    due: dt.datetime
    done: bool
    alerted: bool
    cancelled: bool
    revision: int

HOURS = {'zero': 0, 'uma': 1, 'um': 1, 'duas': 2, 'dois': 2, 'tres': 3, 'quatro': 4,
         'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10,
         'onze': 11, 'doze': 12, 'treze': 13, 'catorze': 14, 'quatorze': 14,
         'quinze': 15, 'dezesseis': 16, 'dezessete': 17, 'dezoito': 18, 'dezenove': 19,
         'vinte': 20, 'vinte e uma': 21, 'vinte e um': 21, 'vinte e duas': 22,
         'vinte e dois': 22, 'vinte e tres': 23}
DAY = re.compile(r'\b(hoje|amanha|\d{2}/\d{2}/\d{4})\b')
TIME = re.compile(r'\bas\s+(?:(?P<hour>\d{1,2})(?::(?P<minute>\d{2})|h(?P<hminute>\d{2})?)?'
                  r'|(?P<word>' + '|'.join(sorted(HOURS, key=len, reverse=True)) + r')'
                  r'(?:\s+e\s+(?P<fraction>meia|quinze))?)(?![\w:]|\.\d)')
UNSUPPORTED_MINUTES = re.compile(r'\s+(?:\d+\b|e\s+(?:\d+|' + '|'.join(HOURS) + r'|trinta|quarenta|cinquenta)\b)')

def parse_reminder(text, now=None):
    """Accept a small, explicit vocabulary; never guess a missing time."""
    return schedule_parts(text, now)[0]


def schedule_parts(text, now=None):
    """Return a due date and normalized non-temporal words, never inferred fields."""
    now = now or dt.datetime.now()
    clean = normalize(text)
    days, times = list(DAY.finditer(clean)), list(TIME.finditer(clean))
    if not days:
        raise ValueError('Qual é a data? Informe hoje, amanhã ou DD/MM/AAAA.')
    if not times:
        raise ValueError('Qual é o horário? Informe, por exemplo, “às 10h” ou “às dez”.')
    if len(days) != 1 or len(times) != 1:
        raise ValueError('Informe uma única data e um único horário para este lembrete.')
    day, time = days[0], times[0]
    suffix = clean[time.end():]
    if re.match(r'\s+(?:da|de)\s+(?:manha|tarde|noite|madrugada)\b', suffix) or UNSUPPORTED_MINUTES.match(suffix):
        raise ValueError('Use o horário no formato de 24 horas, como “às 22:30”.')
    if day[1] in ('hoje', 'amanha'):
        date = now.date() + dt.timedelta(days=int(day[1] == 'amanha'))
    else:
        date = dt.datetime.strptime(day[1], '%d/%m/%Y').date()
    hour = int(time['hour']) if time['hour'] is not None else HOURS[time['word']]
    minute = int(time['minute'] or time['hminute'] or 0)
    if time['fraction']:
        minute = 30 if time['fraction'] == 'meia' else 15
    due = dt.datetime.combine(date, dt.time(hour, minute))
    if due <= now:
        raise ValueError('Esse horário já passou. Informe uma data e hora futuras.')
    remainder = TIME.sub('', DAY.sub('', clean)).strip(' ,.;:-')
    return due, remainder


