from calendar import HTMLCalendar, monthrange
from datetime import datetime
from django.utils.safestring import SafeString
from django.urls import reverse
from .models import Transaction

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

        month_int = int(month)

        html_code = "<table class='calendar'>\n"
        html_code += f"  <tr><th colspan='7'>{year} {self.month_name[month_int]}</th></tr>\n"
        html_code += "  <tr><th class='mon'>Mon</th><th class='tue'>Tue</th><th class='wed'>Wed</th><th class='thu'>Thu</th><th class='fri'>Fri</th><th class='sat'>Sat</th><th class='sun'>Sun</th></tr>\n"

    
        first_day = datetime(year, month_int, 1)


        first_weekday = first_day.weekday()


        days_in_month = self.monthrange(year, month_int)[1]

        current_date = datetime.now().date()

        transactions = Transaction.objects.filter(transaction_date__year=year, transaction_date__month=month_int)


        days_with_transactions = {day: False for day in range(1, days_in_month + 1)}


        for transaction in transactions:
            transaction_day = transaction.transaction_date.day
            days_with_transactions[transaction_day] = True


        num_weeks = (days_in_month + first_weekday) // 7
        if (days_in_month + first_weekday) % 7 > 0:
            num_weeks += 1


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
                    has_transactions = 'transaction-day' if days_with_transactions[current_day] else ''
                    
                    dots = ''
                    if days_with_transactions[current_day]:
                        income_transactions = [transaction for transaction in transactions if transaction.transaction_date.day == current_day and transaction.is_income]
                        expense_transactions = [transaction for transaction in transactions if transaction.transaction_date.day == current_day and not transaction.is_income]
                        
                        if income_transactions and expense_transactions:
                            dots = 'income-dot expense-dot'
                        elif income_transactions:
                            dots = 'income-dot'
                        elif expense_transactions:
                            dots = 'expense-dot'

                    html_code += f"    <td class='{self.cssclasses[day]} {cell_class} {has_transactions} {dots}' id='day-{date.strftime('%Y-%m-%d')}'><a class='day-link' href='{url}'><div class='cell-content'>{current_day}</div></a></td>\n"
            html_code += "  </tr>\n"

        html_code += "</table>\n"

        return SafeString(html_code)
