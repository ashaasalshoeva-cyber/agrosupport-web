"""Transparent demonstrator of wheat N/P2O5/K2O nutrient balance (kg/ha).

This is a bookkeeping balance, not soil-fertility measurement or fertilizer-rate
prescription. Wheat grain/straw removal coefficients are editable DEMO values.
"""
from __future__ import annotations
import math

ELEMENTS=('N','P2O5','K2O')
# Hypothetical scenario values, not a soil assay or regional recommendation.
DEMO_GRAIN={'N':22.0,'P2O5':9.0,'K2O':6.0}  # kg per tonne harvested grain
DEMO_STRAW={'N':5.0,'P2O5':2.0,'K2O':15.0}  # kg per tonne straw exported


def finite_number(value,name,lower=0,upper=1_000_000):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(f'{name}: ожидается число')
    if not lower<=value<=upper:
        raise ValueError(f'{name}: допустимый диапазон {lower}–{upper}')
    return float(value)


def nutrients(value,label,upper=1500):
    if not isinstance(value,dict):
        raise ValueError(f'{label}: ожидается объект с N, P2O5, K2O')
    return {e:finite_number(value.get(e),f'{label}.{e}',0,upper) for e in ELEMENTS}


def calculate_balance(data):
    """Return nutrient inventory change by simple inputs-minus-outputs accounting.

    Fertilizer/organic inputs = TOTAL declared nutrients, NOT season-available share.
    Grain and exported straw are subtracted; straw retained in the field does not
    count as a *new* nutrient input (avoids double counting).
    """
    if not isinstance(data,dict):raise ValueError('Ожидается объект параметров')
    area=finite_number(data.get('area_ha'),'area_ha',0.01,100_000)
    yield_t=finite_number(data.get('yield_t_ha'),'yield_t_ha',0.1,25)
    straw_ratio=finite_number(data.get('straw_ratio',1.1),'straw_ratio',0,4)
    straw_exported=data.get('straw_exported',False)
    if not isinstance(straw_exported,bool):raise ValueError('straw_exported: ожидается true или false')
    grain=nutrients(data.get('grain_offtake_kg_t',DEMO_GRAIN),'grain_offtake_kg_t',100)
    straw=nutrients(data.get('straw_offtake_kg_t',DEMO_STRAW),'straw_offtake_kg_t',100)
    mineral=nutrients(data.get('mineral_kg_ha'),'mineral_kg_ha')
    organic=nutrients(data.get('organic_kg_ha'),'organic_kg_ha')
    losses=nutrients(data.get('estimated_loss_kg_ha'),'estimated_loss_kg_ha')
    rows={}
    for e in ELEMENTS:
        removal_grain=yield_t*grain[e]
        removal_straw=(yield_t*straw_ratio*straw[e]) if straw_exported else 0.
        inputs=mineral[e]+organic[e]
        outputs=removal_grain+removal_straw+losses[e]
        balance=inputs-outputs
        rows[e]={
            'inputs_kg_ha':round(inputs,2),
            'grain_offtake_kg_ha':round(removal_grain,2),
            'straw_export_kg_ha':round(removal_straw,2),
            'losses_kg_ha':round(losses[e],2),
            'balance_kg_ha':round(balance,2),
            'balance_total_kg':round(balance*area,2),
            'replacement_gap_kg_ha':round(max(0.,-balance),2),
        }
    return {
        'crop':'wheat','area_ha':area,'yield_t_ha':yield_t,
        'straw_exported':straw_exported,'straw_ratio':straw_ratio,
        'elements':rows,'method':'declared nutrient inputs minus grain/straw exports and estimated losses',
        'data_origin':'editable illustrative parameters + farmer entries; NOT NASA soil NPK',
        'limitations':[
          'Нулевой или положительный баланс не доказывает восстановления плодородия почвы.',
          'Содержание доступных элементов, pH, засоление и органическое вещество требуют лабораторных анализов.',
          'Поступление органических удобрений учитывается по их ПОЛНОМУ составу; доступность по сезонам здесь не моделируется.',
          'Потери из-за вымывания, газовых выделений и эрозии необходимо оценивать отдельно; ноль означает неизвестно/не задано.',
          'Коэффициенты выноса зерном и соломой демонстрационные; агроном должен заменить их региональными значениями.'
        ]
    }


def basic_advice(balance,weather=None):
    elements=balance['elements']; negatives=[(e,row['replacement_gap_kg_ha']) for e,row in elements.items() if row['replacement_gap_kg_ha']>0]
    positives=[(e,row['balance_kg_ha']) for e,row in elements.items() if row['balance_kg_ha']>0]
    parts=[]
    if negatives:
        parts.append('Расчётный дефицит баланса: '+', '.join(f'{e} {v:.1f} кг/га' for e,v in negatives)+'. Это оценка для планирования, не готовая доза удобрений.')
    else:parts.append('По введённым данным отрицательного NPK-баланса нет; это не свидетельствует о восстановлении плодородия.')
    if positives:parts.append('Положительный баланс: '+', '.join(f'{e} {v:.1f} кг/га' for e,v in positives)+'. Избыток поступления также требует проверки экологических рисков.')
    if balance['straw_exported']:
        parts.append('Вывоз соломы увеличивает вынос особенно калия. Рассмотрите возврат растительных остатков, если это совместимо с условиями поля.')
    else:parts.append('Солома оставлена на поле и не вычитается как экспорт; доступность веществ при разложении не мгновенна.')
    if weather:
        totals=weather.get('totals',{});rain=totals.get('rain_mm')
        if rain is not None:
            parts.append(f'NASA POWER: осадки за выбранный ИСТОРИЧЕСКИЙ период ≈ {rain:.1f} мм. Это климатические данные, не измерение почвенного NPK и не прогноз.')
    else:parts.append('Метеоданные NASA не загружены: климатический контекст не учтён.')
    parts.append('Следующий шаг: отбор проб почвы N/P/K, органического вещества, pH и электропроводности; согласование плана с местным агрономом.')
    return ' '.join(parts)
