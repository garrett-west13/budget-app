document.addEventListener('DOMContentLoaded', function() {
    let currentDate = new Date();
    let currentYear = currentDate.getFullYear();
    let currentMonth = currentDate.getMonth();

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
});


function loadCalendarContent(year, month) {
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


document.addEventListener('DOMContentLoaded', function() {
    // Get the recurring checkbox element
    const recurringCheckbox = document.getElementById('id_recurring');

    // Get the frequency select field element
    const frequencyField = document.getElementById('frequency');

    // Hide the frequency field initially
    frequencyField.style.display = 'none';

    // Add an event listener to the recurring checkbox
    recurringCheckbox.addEventListener('change', function() {
        // If the recurring checkbox is checked, show the frequency field, otherwise hide it
        if (this.checked) {
            frequencyField.style.display = 'block';
        } else {
            frequencyField.style.display = 'none';
        }
    });
});