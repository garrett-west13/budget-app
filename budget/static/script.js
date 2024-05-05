document.addEventListener('DOMContentLoaded', function() {
    // Retrieve the selected month and year from local storage, or use the current month and year if not available
    let currentDate = new Date();
    let currentYear = currentDate.getFullYear();
    let currentMonth = currentDate.getMonth();

    const storedMonth = localStorage.getItem('selectedMonth');
    const storedYear = localStorage.getItem('selectedYear');

    if (storedMonth && storedYear) {
        currentMonth = parseInt(storedMonth);
        currentYear = parseInt(storedYear);
    }

    // Fetch and load the initial calendar HTML
    loadCalendarContent(currentYear, currentMonth);

    // Event listener for navigating to the previous month
    document.getElementById('prev-month').addEventListener('click', function() {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        loadCalendarContent(currentYear, currentMonth);
    });

    // Event listener for navigating to the next month
    document.getElementById('next-month').addEventListener('click', function() {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        loadCalendarContent(currentYear, currentMonth);
    });

    // Event listener for going back to the current month
    document.getElementById('current-month').addEventListener('click', function() {
        // Reset to the current month and year
        currentDate = new Date();
        currentYear = currentDate.getFullYear();
        currentMonth = currentDate.getMonth();
        
        // Load the calendar content for the current month
        loadCalendarContent(currentYear, currentMonth);
    });

    // Store the selected month and year in local storage
    function storeSelectedMonthAndYear(year, month) {
        localStorage.setItem('selectedMonth', month);
        localStorage.setItem('selectedYear', year);
    }

    // Load the calendar content and store the selected month and year
    function loadCalendarContent(year, month) {
        storeSelectedMonthAndYear(year, month);
        fetch(`/calendar/${year}/${month + 1}/`)
            .then(response => {
                return response.text();
            })
            .then(data => {
                document.getElementById('calendar').innerHTML = data;
            })
            .catch(error => {
                console.error('Error fetching calendar content:', error);
            });
    }
});

