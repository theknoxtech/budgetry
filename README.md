# Budgetry: Personal Finance CLI

![Budgetry Main Menu](https://raw.githubusercontent.com/theknoxtech/budgetry/main/assets/main_menu.png)

A simple yet powerful command-line application for managing your personal finances. Track your spending, categorize expenses, and stay on top of your budget with an intuitive, terminal-based interface.

## About The Project

Budgetry was built to provide a straightforward, keyboard-driven way to manage your finances without the clutter of web interfaces or subscription fees. It's designed for those who are comfortable working in a terminal and prefer a local-first approach to their data.

The application stores all financial data locally in a `budget.db` SQLite database file, ensuring you always have full ownership and control of your information.

## Features

-   **Transaction Management**: Add, edit, or delete transactions with details like date, payee, amount, and a descriptive memo.
-   **Custom Categories**: Create personalized spending categories to organize your transactions effectively.
-   **Payee Management**: Maintain a list of common payees for quick and consistent data entry.
-   **Local First**: All your data is stored locally. No cloud, no subscriptions, no privacy concerns.
-   **(In Progress)**: Detailed financial reports to visualize your spending habits.

## Getting Started

Follow these steps to get a local copy up and running.

### Prerequisites

-   Python 3.7+

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/theknoxtech/budgetry.git
    ```
2.  **Navigate to the project directory:**
    ```sh
    cd budgetry
    ```
3.  **Create and activate a virtual environment:**
    - On macOS and Linux:
      ```sh
      python3 -m venv .venv
      source .venv/bin/activate
      ```
    - On Windows:
      ```sh
      python -m venv .venv
      .venv\Scripts\activate
      ```
4.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

## Usage

To start the application, run `main.py` from the `app` directory:

```sh
python app/main.py
```

You will be greeted with the main menu. From there, you can navigate to different sections of the application by entering the corresponding number.

-   **Manage Transactions**: View, add, edit, or delete your income and expense records.
-   **Manage Categories**: Define the categories you want to sort your transactions into.
-   **Manage Payees**: Keep a clean list of people and businesses you transact with.

## Future Development

The vision for Budgetry extends beyond the command line. The next major milestone is to transform it into a full-featured, cross-platform desktop application.

-   **GUI Application**: The project will be evolving into a graphical user interface using the **CustomTkinter** library, providing a more visual and user-friendly experience.
-   **Reporting**: The "Reports" section is under active development and will soon provide insights into your financial habits.

