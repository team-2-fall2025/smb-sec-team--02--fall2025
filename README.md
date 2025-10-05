# AI-Augmented Cyber Risk & Threat Intelligence Framework for SMBs

## Project One-Liner
A security-focused web application for small-medium businesses, providing robust backend APIs and a user-friendly React frontend with MongoDB for flexible data storage,  web-based, agentic-AI platform SMBs can configure to (1) identify assets, (2) ingest OSINT + logs, (3) score & prioritize risk, and (4) automate security workflows mapped to NIST CSF 2.0

## Team Roster & Roles
| Name              | Email                     | Role(s)                        |
|-------------------|---------------------------|--------------------------------|
| Ramzey Alissa     | rag9w@umsystem.edu        | Team Lead / risk & compliance  |
| Weikang Ding      | dingweik@msu.edu          | risk & compliance              |
| Binhao Ma         | 1145183478@qq.com         | Frontend / Backend             |
| Immanuel Olaoye   | olaoye939@gmail.com       | Frontend / Backend             |

## Quickstart for Backend & Frontend (Local Run)

### Prerequisites
- **Python 3.11**
- **Node.js 20**
- **MongoDB**

### Backend Commands ###
run commands after naviagting to **src/backend** :

- **python -m venv .venv**: Setup virtual envirinment for python so the dependencies remain seperate reducing errors.
- **source .venv/Scripts/activate**: Set source directory for virtual environment for Windows.
- **source .venv/bin/activate**: Set source directory for virtual environment for Linux/Mac.
- **pip install -r requirements.txt**: Install all required python dependencies.
- **uvicorn app:app --reload --port 8000**: Run the app with uvicorn on port 8000 (local) on autoreload mode for development.


### Frontend Commands ###
run commands after naviagting to **src/frontend** :

- **npm install**: Install all required packages using npm.
- **npm run dev**: Runs the react app in dev mode on port 5173 (local).

### Run Both Frontend and Backend Apps with a script ###
In project root folder run the start-app.bat script with the following command:
- **./start-app.bat**: will run all the previous commands in a script in two new terminals, exit the terminals to shut them off.

### How to Set Environment Variables ###
Environment variables are required for MongoDB connections, API keys, and configuration. Set them based on your operating system.

- **set \<var-name>=\<value>**:in windows (Command Prompt)
- **export \<var-name>=\<value>**:in Linux/Mac 



# 🗃️ Database Configuration Guide

## 📌 Environment Information
- **Database Type:** MongoDB  
- **Port:** `27017`  
- **Operating System:** Windows  

---

## ⚙️ Database Setup and Data Import Steps

1. **Ensure MongoDB Service is Running**  
   - Start the MongoDB service (you can do this via `services.msc` or using the command line:  
     ```
     net start MongoDB
     ```
   - The default listening port is `27017`.

2. ### 🧩 Database Seeding from CSV

To initialize the database using the provided CSV datasets, run the following command:


| Function                | Method | Test URL |
|-------------------------|---------|----------|
| Initialize the database | `GET` | http://127.0.0.1:8000/api/db/seed |




## 🧪 API Test Endpoints

| Function | Method | Test URL |
|-----------|---------|----------|
| Insert Data Test | `POST` | [http://127.0.0.1:8000/api/osint/test](http://127.0.0.1:8000/api/osint/test) |
| Statistics Test | `GET` | [http://127.0.0.1:8083/api/stats](http://127.0.0.1:8083/api/stats) |

> ⚠️ **Before testing**, make sure the test data has been successfully imported into MongoDB.

---

## ✅ Example Testing Workflow

1. Start the MongoDB service.  
2. Run code.
3. Initialize the database http://127.0.0.1:8000/api/db/seed.  
4. Use your browser or Postman to access:
   - Insert test data → `http://127.0.0.1:8000/api/osint/test`  
   - Check statistics → `http://127.0.0.1:8083/api/stats`

---

## 💡 Notes
- If you encounter a connection error, ensure the MongoDB service is running correctly.  
- If you change the database name or port, make sure to update your project configuration file (such as `.env` or `config.js`).

---
