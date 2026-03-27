I# InsightSQL-AI


[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)  
[![React](https://img.shields.io/badge/React-18-blueviolet)](https://reactjs.org/)  


**InsightSQL-AI** is a platform that generates SQL queries and provides insights from analytical questions written in natural language. It combines AI-powered suggestions, question validation, and a query history to accelerate data analysis.


---


## 🔹 Key Features


- Automatic generation of **SQL queries** from natural language questions.  
- AI-powered suggestions for analytical questions based on **keywords**.  
- Validation to ensure questions have **analytical meaning**.  
- Query history with easy reuse of previous queries.  
- Visualization of SQL results and AI-generated insights.  
- Full **React frontend + Django backend** integration.  


---


## 🛠 Technologies


- **Frontend:** React, Tailwind CSS, Vite  
- **Backend:** Django 6, Python 3.12  
- **Database:** PostgreSQL / SQLite  
- **AI Services:** Azure OpenAI or any text generation engine  
- **Others:** LocalStorage for query history, REST APIs  


---


## 💻 Installation


### 1. Clone the repository
```bash
git clone https://github.com/evymari/InsightSQL-AI.git
cd InsightSQL-AI


💻 Installation
1. Clone the repository
git clone https://github.com/evymari/InsightSQL-AI.git
cd InsightSQL-AI
2. Setup backend
cd backend
python -m venv venv
# Activate virtual environment
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
3. Setup frontend
cd ../frontend
npm install
npm run dev


The application will be available at:


http://localhost:5173


🚀 Usage
Type a keyword or question in the search bar.
Click Suggest Question to get analytical query suggestions.
Select a suggestion to automatically generate the SQL query.
View the SQL query and the AI-generated insight.
Previous queries are automatically saved in the history.


🧩 Example Flow


User input:


electronics product sales


Generated suggestions:


How many electronics products were sold this month?
Which electronics product had the highest sales?
What is the sales trend for electronics in the last 6 months?


Generated SQL query (example):


SELECT product_name, SUM(quantity) AS total_sales
FROM sales
WHERE category='Electronics'
GROUP BY product_name
ORDER BY total_sales DESC;
```
```


🏗 Project Structure
InsightSQL-AI/
├─ backend/
│  ├─ main_app/
│  │  ├─ views.py       # Endpoints and AI logic
│  │  └─ urls.py
│  ├─ manage.py
│  └─ requirements.txt
├─ frontend/
│  ├─ pages/
│  │  ├─ Dashboard.jsx
│  │  └─ History.jsx
│  ├─ components/
│  │  ├─ Sidebar.jsx
│  │  ├─ QueryForm.jsx
│  │  └─ Results.jsx
│  ├─ api.js            # Backend connection
│  └─ utils/
└─ README.md
```
## 📊 Dashboard

![Dashboard](frontend\docs\images\dashboard.png)

## 💡 AI Suggestions

![Suggestions](frontend\docs\images\suggestions.png)

## 📈 Results

![Results](frontend\docs\images\results.png)

## 👥 Development Team


**InsightSQL-AI** is developed and maintained by a passionate team of software engineers and AI specialists:


| Name | Role | Contact |
|------|------|---------|
| Evy Maritza Quevedo | Full-Stack Developer & Project Lead | [Email](mailto:evymaritza@hotmail.com) \| [LinkedIn](https://www.linkedin.com/in/evelyn-quevedo-garrido/) |
| Stalin Maza | Software Developer (Handytec) | [Email](mailto:stalin_ct97@hotmail.com) \| [LinkedIn](https://www.linkedin.com/in/stalinmazaepn18/) |
| Reewos Talla Chumpitaz | AI & Data Engineer | [Email](mailto:reewos.talla.c@uni.pe) \| [LinkedIn](https://www.linkedin.com/in/reewos-talla-chumpitaz/) |




