# Library Management System

## Description

The Library Management System is a web application designed to help manage a library's collection of e-books. Users can browse the books, rent the books,purchase e-books, and download them in PDF format. The system also provides administrative features for managing users, books, and transactions.

## Technologies Used

- **Python**: Used to develop the backend logic and serve as the host programming language for the application.
- **HTML/CSS**: Utilized to create and style the web pages for user interaction.
- **Bootstrap**: Employed to enhance the frontend appearance and improve navigation.
- **SQLite**: Serves as the database management system for storing and retrieving book and user information.
- **Flask**: Used as the web framework to handle routing, requests, and responses.
- **Flask-SQLAlchemy**: Integrated for simplified interaction with the SQLite database.
- **Git**: Employed for version control and collaborative development.

## Features

- **User Authentication**: Sign up and log in functionalities to access the system.
- **Browse Catalog**: Users can explore the available e-books in the library catalog.
- **Admin Panel**: Administrative features for managing users, books, and transactions.
- **Search and Filtering**: Users can search for specific books and filter by categories or book titles.
- **Purchase and Download**: Users can purchase e-books and download them in PDF format for a price.
- **Responsive Design**: The application is designed to be accessible and usable across various devices.
- **Data Visualization with Plotly**: Utilizes Plotly for interactive data visualization, providing insightful      graphs and charts to visualize library statistics, user engagement, or any other relevant data

## RESTful API

- The application offers a RESTful API, facilitating access to various functionalities through HTTP endpoints.
- Token-based authentication is enforced for specific requests that necessitate authorization, ensuring secure access to protected resources.

## Installation and Usage

1. Clone the repository to your local machine:

    ```bash
    git clone <repository-url>
    ```

2. Navigate to the project directory:

    ```bash
    cd <project-directory>
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:

    ```bash
    python app.py
    ```

5. Access the application in your web browser at `http://localhost:5000`.


