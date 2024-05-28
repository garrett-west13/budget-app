# Budget Project

#### [Video Demo](https://youtu.be/5HQr3RCUB68)

### Distinctiveness and Complexity

#### Distinctiveness
The Budget Project offers a tailored solution for personal finance management, focusing on the specific needs of users who prioritize financial planning and tracking.

#### Complexity
The project achieves complexity through advanced backend logic, interactive frontend components, and responsive design principles.

1. **Robust Backend Architecture**: Utilizing Django, the backend efficiently handles server-side operations, ensuring seamless data management.
2. **Interactive Frontend Elements**: Incorporating JavaScript, HTML, and CSS, the application delivers dynamic and interactive user interfaces.
3. **Responsive Design Principles**: Following a mobile-first approach, the application ensures responsiveness across various devices.
4. **Advanced User Authentication and Authorization**: Robust mechanisms secure sensitive financial data, including password hashing and role-based access control.
5. **Comprehensive Testing and Documentation**: Extensive documentation provides clear instructions on setup, configuration, and usage.

## File Structure

- **/budget_app**: Main directory containing the Django project.
  - **/budget**: Django app directory containing models, views, forms, templates, and static files.
  - **manage.py**: Django management script.

## How to Run

To run the application locally:

1. Clone the project repository.
2. Navigate to the project directory.
3. Install dependencies with `pip install -r requirements.txt`.
4. Configure database settings in `budget_app/settings.py`.
5. Run Django migrations with `python manage.py migrate`.
6. Start the Django development server with `python manage.py runserver`.
7. Access the application at `http://localhost:8000`.

## Deployment to Heroku

The Budget Project is deployed to Heroku for seamless hosting and scalability. The application leverages Heroku's managed PostgreSQL service and integrates with AWS S3 for static file storage. The deployment process ensures reliability and performance for users accessing the application from various locations.

## Additional Information

- **Database**: The application uses SQLite as the default backend but can be configured for other databases supported by Django.
- **Dependencies**: Additional Python packages required are listed in `requirements.txt`.

## Conclusion

The Budget Project delivers a unique and complex web application built with Django and JavaScript, providing a robust and user-friendly solution for personal finance management.

## License

[MIT License]()
