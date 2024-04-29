from calendar import HTMLCalendar, monthrange
from datetime import datetime
from django.utils.safestring import SafeString
from django.urls import reverse

class Calendar(HTMLCalendar):

    month_name = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    def __init__(self):
        super().__init__()


    def monthrange(self, year, month):
        return monthrange(year, month)

    def formatmonth(self, year, month):
        if not isinstance(year, int) or not isinstance(month, int):
            raise ValueError("Year and month must be integers")

        # Convert month to an integer
        month_int = int(month)

        # Generate the HTML code for the calendar
        html_code = "<table>\n"
        html_code += f"  <tr><th colspan='7'>{year} {self.month_name[month_int]}</th></tr>\n"
        html_code += "  <tr><th class='mon'>Mon</th><th class='tue'>Tue</th><th class='wed'>Wed</th><th class='thu'>Thu</th><th class='fri'>Fri</th><th class='sat'>Sat</th><th class='sun'>Sun</th></tr>\n"

        # Get the first day of the month
        first_day = datetime(year, month_int, 1)

        # Get the weekday (0-6) of the first day of the month
        first_weekday = first_day.weekday()

        # Get the number of days in the month
        days_in_month = self.monthrange(year, month_int)[1]

        # Get the current date
        current_date = datetime.now().date()

        # Calculate the number of weeks in the month
        num_weeks = (days_in_month + first_weekday) // 7
        if (days_in_month + first_weekday) % 7 > 0:
            num_weeks += 1

        # Generate the rows and cells for the calendar
        for week in range(num_weeks):
            html_code += "  <tr>\n"
            for day in range(7):
                if week == 0 and day < first_weekday:
                    html_code += "    <td class='empty'></td>\n"
                elif day + (week * 7) - first_weekday >= days_in_month:
                    break
                else:
                    current_day = day + 1 + (week * 7) - first_weekday
                    date = datetime(year, month_int, current_day)
                    url = reverse('add_transaction', args=(date.year, date.month, date.day))
                    cell_class = 'current-day' if date.date() == current_date else 'day'
                    html_code += f"    <td class='{self.cssclasses[day]} {cell_class}' id='day-{date.strftime('%Y-%m-%d')}'><a class='day-link' href='{url}'><div class='cell-content'>{current_day}</div></a></td>\n"
            html_code += "  </tr>\n"

        html_code += "</table>\n"

        return SafeString(html_code)
