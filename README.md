# AI-First CRM HCP Module – Log Interaction Screen

An AI-powered Customer Relationship Management (CRM) system focused on the Healthcare Professional (HCP) module. Built for field representatives in life sciences to log, manage, and analyze their interactions with healthcare professionals.

![Tech Stack](https://img.shields.io/badge/React-18-61DAFB?logo=react) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi) ![LangGraph](https://img.shields.io/badge/LangGraph-AI_Agent-FF6B6B) ![Groq](https://img.shields.io/badge/Groq-gemma2--9b--it-6C63FF)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Structured   │  │   AI Chat    │  │  Dashboard   │  │
│  │    Form       │  │  Interface   │  │   & Lists    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │           │
│         └────────┬────────┴──────────┬───────┘          │
│                  │  Redux Store      │                   │
│         ┌────────┴──────────────────┴────────┐          │
│         │         Axios API Layer             │          │
└─────────┼────────────────────────────────────┼──────────┘
          │           REST API                 │
┌─────────┼────────────────────────────────────┼──────────┐
│         │        FastAPI Backend              │          │
│  ┌──────┴───────────────────────────┴──────┐           │
│  │            API Routes                    │           │
│  │  /interactions  /hcps  /agent/chat       │           │
│  └──────────────────┬──────────────────────┘           │
│                     │                                    │
│  ┌──────────────────┴──────────────────────┐           │
│  │         LangGraph AI Agent               │           │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ │           │
│  │  │  Log    │ │  Edit    │ │  Search  │ │           │
│  │  │Interact.│ │Interact. │ │Interact. │ │           │
│  │  └─────────┘ └──────────┘ └──────────┘ │           │
│  │  ┌─────────┐ ┌──────────┐              │           │
│  │  │  HCP    │ │ Suggest  │              │           │
│  │  │ Profile │ │Next Action│              │           │
│  │  └─────────┘ └──────────┘              │           │
│  └──────────────────┬──────────────────────┘           │
│                     │ Groq API (llama-3.1-8b-instant)           │
│  ┌──────────────────┴──────────────────────┐           │
│  │         SQLite/PostgreSQL                │           │
│  │   HCPs │ Interactions │ Products         │           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Features

### Log Interaction Screen (Core Feature)
- **Dual Mode Interface**: Switch between a structured form and an AI-powered conversational chat
- **Structured Form**: Complete form with HCP selection, interaction type, notes, product tagging, sentiment analysis, and follow-up scheduling
- **AI Chat Interface**: Natural language interaction logging powered by LangGraph agent
- **AI-Powered Processing**: Automatic summarization, entity extraction, and sentiment analysis of interaction notes

### LangGraph AI Agent Tools
1. **Log Interaction** – Captures interaction data with LLM-powered summarization, entity extraction, key topic identification, and sentiment analysis
2. **Edit Interaction** – Modifies existing logged interactions with validation and change tracking
3. **Get HCP Profile** – Retrieves comprehensive HCP profiles with interaction history and engagement metrics
4. **Search Interactions** – Searches past interactions by HCP, date range, topic, product, or sentiment
5. **Suggest Next Action** – AI-powered recommendations for next best actions, optimal visit timing, and talking points

### Additional Features
- **Dashboard**: Overview with statistics, recent interactions, and quick actions
- **HCP Management**: View and manage healthcare professional profiles
- **Interaction History**: Searchable, filterable list of all logged interactions
- **Dark Theme UI**: Premium glassmorphism design with smooth animations

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Redux Toolkit, React Router, Framer Motion |
| Styling | CSS3 with Glassmorphism, Google Inter Font |
| Backend | Python 3.10+, FastAPI |
| AI Agent | LangGraph, LangChain |
| LLM | Groq API (llama-3.1-8b-instant) |
| Database | SQLite (dev) / PostgreSQL (prod) |

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Groq API Key** – Get from [Groq Console](https://console.groq.com/)



## 📁 Project Structure

```
ai-crm-hcp-module/
├── README.md
├── .env.example
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Configuration & environment variables
│   ├── database.py           # Database connection & session
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic validation schemas
│   ├── seed_data.py          # Sample data seeder
│   ├── agent/
│   │   ├── state.py          # LangGraph state definition
│   │   ├── tools.py          # 5 LangGraph agent tools
│   │   └── graph.py          # LangGraph StateGraph setup
│   └── routes/
│       ├── interactions.py   # Interaction CRUD endpoints
│       ├── hcp.py            # HCP management endpoints
│       └── agent.py          # AI agent chat endpoints
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx           # React entry point
        ├── App.jsx            # Main app with routing
        ├── App.css            # Comprehensive styles
        ├── store/
        │   ├── store.js       # Redux store config
        │   └── slices/
        │       ├── interactionSlice.js
        │       ├── hcpSlice.js
        │       └── chatSlice.js
        ├── services/
        │   └── api.js         # Axios API client
        └── components/
            ├── Sidebar.jsx
            ├── Dashboard.jsx
            ├── LogInteraction.jsx    # ⭐ Core feature
            ├── InteractionList.jsx
            ├── HCPList.jsx
            ├── HCPDetail.jsx
            └── EditInteractionModal.jsx
```

## 🎨 UI Highlights

- **Dark Theme** with gradient backgrounds
- **Glassmorphism** cards with backdrop blur effects
- **Smooth Animations** powered by Framer Motion
- **Responsive Design** for all screen sizes
- **Google Inter** font for clean typography
- **Interactive Elements** with hover effects and micro-animations

## 🤖 LangGraph Agent Details

The AI agent uses a **StateGraph** architecture with the following flow:

```
User Message → Agent Node (LLM) → Tool Selection → Tool Execution → Response
                    ↑                                      │
                    └──────────────────────────────────────┘
```

The agent can:
- Understand natural language requests about HCP interactions
- Automatically select the appropriate tool based on context
- Process raw notes into structured data using LLM summarization
- Provide intelligent suggestions based on interaction history

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./crm_hcp.db` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |


