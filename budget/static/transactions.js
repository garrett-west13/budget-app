document.addEventListener('DOMContentLoaded', function() {
    const recurringCheckbox = document.getElementById('id_recurring');
    const frequencyField = document.getElementById('frequencyField');
    const endDateField = document.getElementById('endDateField');
    const inputField = document.getElementById('new_category');
    const selectField = document.getElementById('category');


    document.getElementById('id_recurring').addEventListener('change', function() {
        if (!this.checked) {
            this.removeAttribute('required');
        } else {
            this.setAttribute('required', 'required');
        }
    });

    // Function to handle the recurring checkbox change event
    function handleRecurringChange() {
        frequencyField.style.display = recurringCheckbox.checked ? 'block' : 'none';
        endDateField.style.display = recurringCheckbox.checked ? 'block' : 'none';
    }

    // Function to handle the new category input field change event
    function handleNewCategoryInputChange() {
        selectField.disabled = inputField.value.trim() !== '';
        selectField.value = '';
    }

    recurringCheckbox.addEventListener('change', handleRecurringChange);


    inputField.addEventListener('input', handleNewCategoryInputChange);


    document.getElementById('add-category').addEventListener('click', function(event) {
        const newCategoryInput = document.getElementById('new_category');
        const newCategoryName = newCategoryInput.value.trim();

        if (!newCategoryName) {
            console.error('New category name is empty');
            return;
        }

        const csrfToken = document.getElementsByName('csrfmiddlewaretoken')[0]?.value;

        if (!csrfToken) {
            console.error('CSRF token is missing');
            return;
        }

        fetch('/create_category/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ name: newCategoryName })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Failed to create category');
        })
        .then(data => {
            console.log('Category created:', data);
            

            const selectField = document.getElementById('category');
            const option = document.createElement('option');
            option.text = data.name; 
            option.value = data.id;
            option.selected = true;  
            selectField.appendChild(option);
        

            newCategoryInput.value = '';  

            selectField.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
