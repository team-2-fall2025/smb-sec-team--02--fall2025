** AI-Augmented Cyber Risk & Threat Intelligence Framework for SMBs **

a web-based, agentic-AI platform SMBs can configure to (1) identify assets, (2) ingest OSINT + logs, (3) score & prioritize risk, and (4) automate security workflows mapped to NIST CSF 2.0

** Team Members**

-   Ramzey Alissa: Team Lead / risk & compliance
-   Weikang Ding: risk & compliance
-   Binhao Ma: backend / frontend
-   Immanuel Olaoye: backend / frontend

** Getting Started ** 

*1) Backend*


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