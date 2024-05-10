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

    // Set the value of the date picker input to the current loaded month
    document.getElementById('date-picker').value = `${currentYear}-${(currentMonth + 1).toString().padStart(2, '0')}`;

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

    // Event listener for date picker change
    document.getElementById('date-picker').addEventListener('change', function() {
        
        const selectedDate = new Date(this.value);
        const selectedYear = selectedDate.getFullYear();
        const selectedMonth = selectedDate.getMonth();

        // Load the calendar content for the selected year and month
        loadCalendarContent(selectedYear, selectedMonth);
    });

    // Function to store the selected month and year in local storage
    function storeSelectedMonthAndYear(year, month) {
        localStorage.setItem('selectedMonth', month);
        localStorage.setItem('selectedYear', year);
        const csrftoken = getCookie('csrftoken');
        fetch('/store_selected_month_year/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                selectedMonth: month,
                selectedYear: year
            })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Error storing selected month and year');
            }
        })
        .then(data => {
        })
        .catch(error => {
            console.error(error);
        });
    }

    // Function to get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Check if the cookie contains the CSRF token
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Function to show the loading spinner
    function showLoadingSpinner() {
        const loadingSpinner = document.getElementById('loading-spinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
    }

    // Function to hide the loading spinner
    function hideLoadingSpinner() {
        const loadingSpinner = document.getElementById('loading-spinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }

    // Load the calendar content
    function loadCalendarContent(year, month) {
        // Hide the calendar while loading
        document.getElementById('calendar').style.display = 'none';
        // Show the loading spinner
        showLoadingSpinner();

        document.getElementById('total-expenses').textContent = 'Loading...';
        document.getElementById('total-income').textContent = 'Loading...';
        document.getElementById('total-savings').textContent = 'Loading...';
        document.getElementById('total-balance').textContent = 'Loading...';

        storeSelectedMonthAndYear(year, month);
        fetch(`/calendar/${year}/${month + 1}`)
            .then(response => {
                return response.text();
            })
            .then(data => {
                // Show the calendar after the content is loaded
                document.getElementById('calendar').innerHTML = data;
                document.getElementById('calendar').style.display = 'block';
                updateTotals();

                // Hide the loading spinner after the calendar content is loaded
                hideLoadingSpinner();
            })
            .catch(error => {
                console.error('Error fetching calendar content:', error);
                // Hide the loading spinner in case of an error
                hideLoadingSpinner();
            });
    }

    // Function to fetch totals from the server and update UI
    function updateTotals() {
        fetch('/calculate_totals/')
            .then(response => response.json())
            .then(data => {
                // Update UI with totals
                document.getElementById('total-expenses').textContent = '$' + data.total_expenses;
                document.getElementById('total-income').textContent = '$' + data.total_income;
                document.getElementById('total-savings').textContent = '$' + data.total_savings;

                // Update total balance and add class based on its value
                const totalBalanceElement = document.getElementById('total-balance');
                const totalBalance = parseFloat(data.total_balance);

                // Check if totalBalance is a valid number
                if (!isNaN(totalBalance)) {
                    const formattedBalance = totalBalance >= 0 ? '+' + totalBalance.toFixed(2) : totalBalance.toFixed(2);
                    totalBalanceElement.textContent = '$' + formattedBalance;

                    // Remove existing classes
                    totalBalanceElement.classList.remove('surplus', 'deficit');

                    // Add class based on balance value
                    if (totalBalance > 0) {
                        totalBalanceElement.classList.add('surplus');
                    } else if (totalBalance < 0) {
                        totalBalanceElement.classList.add('deficit');
                    }
                } else {
                    console.error('Invalid total balance:', data.total_balance);
                }
            })
            .catch(error => {
                console.error('Error updating totals:', error);
            });
    }
});
