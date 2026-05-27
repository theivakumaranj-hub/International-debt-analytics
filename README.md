# 🌍 International-debt-analytics
![International Debt Dashboard Preview](Dashboard.png)

## 📌 Project Overview
An end-to-end data pipeline and interactive dashboard analyzing the World Bank's global debt dataset. Built with Python, PostgreSQL, and Streamlit, this project seamlessly bridges data engineering, database management, and interactive visual analytics.

## 🛠️ Tech Stack
* **Database:** PostgreSQL
* **Data Engineering:** Python, Pandas, SQLAlchemy
* **Data Visualization:** Streamlit, Plotly Express
* **Analysis:** Advanced PostgreSQL Queries

## 📂 Repository Structure
* `pipeline.py`: Ingests raw data, establishes the relational database structure, and enforces Primary/Foreign Key constraints.
* `reshape.py`: Cleans historical nulls and utilizes Pandas `.melt()` to convert the wide-format dataset into a clean, long-format structure.
* `international_debt_analysis.sql`: A master script containing 30 analytical queries (Basic, Intermediate, and Advanced) proving database manipulation skills.
* `debt_dashboard.py`: The frontend interactive web application featuring multi-tab visualizations (YoY velocity, Sunburst composition, and trend lines).
* `requirements.txt`: Contains all necessary Python libraries required to run the environment.
* `*.csv`: The raw World Bank dataset included for immediate, plug-and-play execution.

---

## 🚀 Setup & Installation

### 1. Install Dependencies
Open your terminal and run the following command to install the required libraries:

`pip install -r requirements.txt`

2. Execute the Pipeline
(These should be run in the exact order below)

Step A: Build the Database Architecture

`python pipeline.py`

Step B: Clean the Data

`python reshape.py`

Step C: Launch the Dashboard

`streamlit run debt_dashboard.py`
