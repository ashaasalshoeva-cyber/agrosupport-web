"""Deterministic multilingual summaries; never presents a template as an LLM."""
from __future__ import annotations
from agro_calc import is_valid

TEXT={
 'en':{'title':'Verified-data summary', 'none':'No verified climatic indicators are currently loaded.',
       'source':'Data source: NASA POWER daily gridded estimates.',
       'limits':'These are regional grid estimates, not measurements on the field.',
       'review':'Check actual soil moisture and the crop stage on the plot before acting.',
       'no_npk':'This service does not calculate fertilizer or pesticide prescriptions.'},
 'ru':{'title':'Сводка проверяемых данных','none':'Проверенные климатические показатели пока не загружены.',
       'source':'Источник: суточные сеточные оценки NASA POWER.',
       'limits':'Это региональные сеточные оценки, а не измерения на самом поле.',
       'review':'Перед действиями проверьте фактическую влажность почвы и фазу развития культуры.',
       'no_npk':'Сервис не назначает нормы удобрений и пестицидов.'},
 'tg':{'title':'Хулосаи маълумоти санҷишшаванда','none':'Нишондиҳандаҳои иқлимии санҷидашуда ҳанӯз бор нашудаанд.',
       'source':'Манбаъ: баҳодиҳии шабакавии ҳаррӯзаи NASA POWER.',
       'limits':'Инҳо баҳодиҳии минтақавӣ мебошанд, на ченкунии худи майдон.',
       'review':'Пеш аз амал намии воқеии хок ва марҳилаи рушди зироатро тафтиш кунед.',
       'no_npk':'Хизматрасонӣ меъёри нуриҳо ва пестисидҳоро таъин намекунад.'}
}

def summary(bundle,lang='en'):
    lang=lang if lang in TEXT else 'en'; txt=TEXT[lang]
    data=bundle.get('season') or {}
    items=[]
    # Deliberately no numeric claims in the summary. Numbers and their provenance are
    # exposed in evidence_bundle separately to avoid ungrounded generated figures.
    if data.get('valid_days'):
        items.append(txt['source'])
        items.append(txt['limits'])
    else: items.append(txt['none'])
    items.extend((txt['review'],txt['no_npk']))
    return {'mode':'template','summary':' '.join(items),'key_points':items[:2],
            'caveats':items[-2:],'sources':['NASA POWER'] if data.get('valid_days') else [],
            'evidence_bundle':bundle}

import json, math, re
NUM=re.compile(r"(?<![\w])[-+]?\d+(?:[.,]\d+)?")
def valid_numbers(response,bundle):
    # Includes numbers inside dates and IDs as well as numeric values.
    supplied=[float(x.replace(',','.')) for x in NUM.findall(json.dumps(bundle,ensure_ascii=False))]
    output=[float(x.replace(',','.')) for x in NUM.findall(json.dumps(response,ensure_ascii=False))]
    return all(any(math.isclose(x,y,rel_tol=0,abs_tol=0.051) for y in supplied) for x in output)


