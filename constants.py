from datetime import date, timedelta

GRAPH_IMAGE_PATH = "render/d-solo/HukfaHZgk/covid19?orgId=1&panelId=2&width=1000&height=500&tz=Europe%2FMadrid"
VACCINE_IMAGE_PATH = "render/d-solo/TeEplNgRk/covid-vacunas-espana?orgId=1&panelId=2&width=1000&height=500&tz=Europe%2FMadrid"
DAYS_WITHOUT_REPORT = [date(2020, 12, 8), date(2020, 12, 25), date(2021, 1, 1), date(2021, 1, 6), date(2021, 3, 19),
                       date(2021, 10, 12), date(2021, 11, 1), date(2021, 11, 9), date(2021, 12, 6), date(2021, 12, 8),
                       date(2021, 12, 24), date(2021, 12, 31), date(2022, 1, 6), date(2022, 2, 28)]
SPAIN = "España"

INITIAL_DAY_TWO_REPORTS_A_WEEK = date(2022, 3, 14)

# Include in days without report all mondays, wednesdays and thursdays from the 14th of March...
for i in range(0, (date(2022, 3, 30) - INITIAL_DAY_TWO_REPORTS_A_WEEK).days + 1):
    day = INITIAL_DAY_TWO_REPORTS_A_WEEK + timedelta(i)
    if day.weekday() in [0, 2, 3]:
        DAYS_WITHOUT_REPORT.append(day)
