# Валидация NASA POWER ↔ NOAA GHCN (2025)

Станция: USC00251684. Расстояние от пилота SCAL: 9.34 км (точки не совпадают).
Сохранённые реальные источники: https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=USC00251684&startDate=2025-01-01&endDate=2025-12-31&dataTypes=TAVG%2CTMAX%2CTMIN%2CPRCP&units=metric&format=json&includeAttributes=true; https://power.larc.nasa.gov/api/temporal/daily/point?latitude=40.575256&longitude=-98.137824&start=20150101&end=20251231&community=AG&parameters=T2M%2CT2M_MAX%2CT2M_MIN%2CPRECTOTCORR%2CALLSKY_SFC_SW_DWN%2CRH2M%2CWS2M%2CGWETROOT&format=JSON&time-standard=LST

| Переменная | n (дни) | Bias | MAE | RMSE | r |
|---|---:|---:|---:|---:|---:|
| T2M_MAX | 365 | 0.708 | 4.271 | 5.551 | 0.894 |
| T2M_MAX_monthly | 12 | 0.711 | 0.838 | 1.044 | 0.998 |
| T2M_MIN | 365 | 1.912 | 2.854 | 3.861 | 0.956 |
| T2M_MIN_monthly | 12 | 1.910 | 1.910 | 1.985 | 0.999 |
| PRECTOTCORR | 363 | -0.278 | 2.605 | 7.747 | 0.328 |
| PRECTOTCORR_monthly | 11 | -9.234 | 17.790 | 32.616 | 0.892 |
| T2M_vs_station_max_min_proxy | 365 | 1.027 | 2.920 | 3.804 | 0.949 |

**Ограничения.** Nearby station, not collocated with SCAL. NASA POWER uses LST; NOAA station reporting times differ. Daily precipitation agreement can be weaker than monthly. No Tajik ground validation.
T2M compared with (TMAX+TMIN)/2 is an approximation from station extremes, not official TAVG. Direct temperature comparisons are T2M_MAX ↔ TMAX and T2M_MIN ↔ TMIN.
Расхождения осадков на суточном масштабе не скрываются. Выводы касаются этих двух соседних точек и одного года.
Новых измерений не создавалось. Для Таджикистана наземная валидация не проводилась.
