# Enterprise-Contract-Risk-Analyzer
The Enterprise Contract Risk Analyzer is a production-ready LegalTech app that automates commercial contract reviews. Powered by Gemini 2.5 Flash, it instantly extracts key clauses, flags liabilities with severity scoring, and generates legally safe mitigations—all in a premium Streamlit UI secured by Supabase Auth and PostgreSQL
  _____            _                  _      _____ _     _    
 / ____|          | |                | |    |  __ (_)   | |   
| |     ___  _ __ | |_ _ __ __ _  ___| |_   | |__) | ___| | __
| |    / _ \| '_ \| __| '__/ _` |/ __| __|  |  _  / |/ __| |/ /
| |___| (_) | | | | |_| | | (_| | (__| |_   | | \ \ |\__ \   < 
 \_____\___/|_| |_|\__|_|  \__,_|\___|\__|  |_|  \_\_|___/_|\_\
                        Analyzer & Auditor                      


AI-Powered Legal Intelligence for Commercial Contracts

📖 Overview

The Enterprise Contract Risk Analyzer is a full-stack, production-ready LegalTech application designed to automate the review of commercial contracts (NDAs, Service Agreements, Vendor Contracts).
Instead of reading line-by-line, legal teams and business owners can upload a document and instantly receive a structured AI audit. The system extracts key clauses, flags high-risk liabilities, checks compliance against industry standards, and provides alternative, risk-mitigated legal phrasing.

✨ Key Features

🔐 Secure Authentication: User registration and login powered by Supabase Auth.
📄 Smart Document Ingestion: Drag-and-drop PDF and TXT parsing (up to 50,000 characters) via pypdf.
🧠 Cognitive AI Engine: Utilizes Google's Gemini 2.5 Flash API with strict application/json schema enforcement to ensure deterministic, structured risk analysis.
🚦 Severity Scoring: Automatically categorizes identified clauses into High, Medium, and Low risk tiers.
🛡️ Automated Mitigation: Generates legally safer, alternative phrasing for every flagged vulnerability.
🗄️ Persistent Audit Archive: Saves every evaluation dynamically into a dedicated profile session matrix archive in PostgreSQL.
🎨 Premium UI: Custom-built dark mode interface using native Streamlit components, metric cards, and responsive dataframes.

🏗️ Architecture & Data Flow

[ 👤 User / Legal Team ]
          |
          v
[ 🔐 Supabase Auth ] ----> (Validates Session Token)
          |
          v
[ 📄 Upload PDF/TXT ] ---> (Extracted & Cleaned via PyPDF)
          |
          v
[ 🧠 Gemini 1.5 Flash ] -> (Analyzes text, enforces JSON schema)
          |
          v
[ 💾 Supabase DB ] <------ (Saves Audit History & Risk Scores)
          |
          v
[ 📊 Streamlit UI ] -----> (Displays Interactive Metrics & Mitigations)

🛠️ Technology Stack

Component   | Technology    | Description
Frontend UI - 👑 Streamlit - Rapid, data-driven web app framework
Backend Logic - 🐍 Python - Core logic, API orchestration, and PDF parsing
AI Engine - 🤖 Google Gemini - Large Language Model (gemini-2.5-flash)
Database - 🐘 Supabase (PostgreSQL) - Relational data storage & historical logs
Authentication - 🔑 Supabase Auth - Secure, JWT-based user session management

🚀 Local Installation & Setup

Follow these steps to run the application locally on your machine.

1. Clone the Repository
  git clone [https://github.com/yourusername/enterprise-contract-risk-analyzer.git](https://github.com/yourusername/enterprise-contract-risk-analyzer.git)
cd enterprise-contract-risk-analyzer
2. Install Dependencies
  Ensure you have Python 3.9+ installed, then run:
  pip install -r requirements.txt
3. Environment Variables
  Create a .env file in the root directory and add your API keys:
  SUPABASE_URL=[https://your-project.supabase.co](https://your-project.supabase.co)
  SUPABASE_ANON_KEY=your_supabase_anon_key
  GEMINI_API_KEY=your_google_gemini_api_key
4. Database Setup
  Create a free project at Supabase.
  Navigate to the SQL Editor in your Supabase dashboard.
  Copy the entire contents of supabase_migration.sql and run it. This will automatically create your profiles table, contract_logs table.
5. Run the Application
  Launch the Streamlit server:
  streamlit run app.py
  The application will open automatically in your browser at http://localhost:8501.
🌐 Deployment (Streamlit Community Cloud)
  This app is fully optimized for free deployment on Streamlit Community Cloud.
  Push this repository to your GitHub account.
  Go to share.streamlit.io and create a new app.
  Select your repository and set the main file path to app.py.
  Go to Advanced Settings -> Secrets and paste your environment variables in TOML format:

  SUPABASE_URL = "[https://your-project.supabase.co](https://your-project.supabase.co)"
  SUPABASE_ANON_KEY = "your_supabase_anon_key"
  GEMINI_API_KEY = "your_google_gemini_api_key"
  Click Deploy! 🎉

🤝 Contributing
  Contributions, issues, and feature requests are welcome! Feel free to check issues page.
