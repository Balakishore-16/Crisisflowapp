# 🚨 CrisisFlow

## AI-Powered Real-Time Emergency Response & Resource Optimization Platform

> CrisisFlow doesn't just tell emergency commanders what is happening. It tells them **what to do next — and explains why.**

CrisisFlow is a Microsoft Fabric-powered AI emergency decision-intelligence platform that converts real-time emergency events into explainable resource-allocation and response decisions.

---

## 🏗️ Architecture

```
React Command Center → FastAPI Backend → Microsoft Fabric Eventstream
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                              Eventhouse/KQL        Lakehouse
                              (Real-Time)          (Historical)
                                    │                   │
                                    ▼                   ▼
                           Real-Time Dashboard   Fabric Notebooks
                                    │                   │
                                    ▼                   ▼
                              Activator             Power BI
                             (Alerts)            (Analytics)
                                    │
                                    ▼
                           AI Decision Engine
                                    │
                                    ▼
                        Explainable Recommendation
                                    │
                                    ▼
                          Commander Dispatch
```

## ✨ Key Features

- **Real-Time Command Center** — Live emergency dashboard with interactive map
- **AI Decision Engine** — Multi-factor resource optimization (not random selection)
- **Explainable AI** — Every recommendation includes transparent reasoning
- **Microsoft Fabric Integration** — Eventstream, Eventhouse, Lakehouse, Power BI
- **5 Emergency Types** — Fire, Accident, Medical, Flood, Industrial
- **Live Simulation** — Realistic demo data with background updates
- **Dispatch System** — Real state changes across incidents, resources, hospitals
- **WebSocket Real-Time** — No manual refresh needed
- **Analytics Dashboard** — Recharts-powered insights from actual data
- **Report Generation** — Printable emergency incident reports

## 🚀 Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## 🎬 Demo Scenario

1. Open CrisisFlow Command Center
2. View normal city operations (4 incidents, 0 critical)
3. Click **🔥 Simulate Building Fire**
4. Watch the full pipeline:
   - 🔥 Fire detected at Tower A, Floor 7, 85 people at risk
   - 🧠 AI classifies as Critical, Spread Risk: High
   - 🚒 Station Bravo selected (lowest effective response time)
   - 🚑 Ambulance assigned
   - 🏥 City Hospital recommended (burn/trauma capacity)
   - 🛣️ Route selected, ETA calculated
   - 🎯 92% confidence with transparent reasoning
5. Click **🚨 DISPATCH RESPONSE**
6. Watch real-time status updates across all resources
7. View updated analytics and reports

## 📁 Project Structure

```
crisisflow/
├── frontend/          # React + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── pages/     # Dashboard, Incidents, Resources, etc.
│   │   ├── components/# Layout, shared components
│   │   ├── services/  # API client
│   │   ├── hooks/     # WebSocket hook
│   │   └── types/     # TypeScript interfaces
├── backend/           # Python + FastAPI
│   ├── app/
│   │   ├── api/       # REST endpoints
│   │   ├── services/  # Decision engine, AI, Fabric, Simulation
│   │   ├── realtime/  # WebSocket manager
│   │   └── models.py  # SQLAlchemy models
│   ├── main.py        # FastAPI app
│   └── seed.py        # Database seeder
├── fabric/            # Microsoft Fabric configs
│   ├── kql/           # Eventhouse table schemas & queries
│   ├── notebooks/     # PySpark analytics notebook
│   ├── eventstream/   # Eventstream setup guide
│   ├── lakehouse/     # Star schema definition
│   └── activator/     # Alert rules
├── powerbi/           # Power BI report specification
└── .env.example       # Environment variables template
```

## 🔧 Microsoft Fabric Setup

1. **Eventstream**: Create `crisisflow-events`, add Custom App source
2. **Eventhouse**: Create KQL database, run `fabric/kql/tables_and_queries.kql`
3. **Lakehouse**: Create tables per `fabric/lakehouse/schema.md`
4. **Notebook**: Import `fabric/notebooks/emergency_analytics.py`
5. **Activator**: Configure rules per `fabric/activator/rules.md`
6. **Power BI**: Build report per `powerbi/report_specification.md`
7. Set `.env` variables with Fabric connection strings

## 🔒 Security

- API keys stored in environment variables only
- Backend-only Fabric/AI communication
- No secrets in frontend code
- `.env.example` provided (never commit `.env`)

## 📊 Decision Engine

The engine scores resources using:
- **Distance** (haversine calculation)
- **Traffic** (congestion levels)
- **Availability** (current status)
- **Equipment** (match with incident type)
- **Severity** (weighted urgency)
- **Hospital Capacity** (specialization match)
- **Response Time** (combined ETA)

AI **explains** the decision — it does not make it.

## 🌐 Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy, SQLite |
| Real-Time | WebSocket, Fabric Eventstream |
| Analytics | Recharts, Fabric Notebooks, Power BI |
| AI | Local Engine + Azure AI Foundry (optional) |
| Storage | SQLite (local), Fabric Lakehouse/Eventhouse |
| Maps | React Leaflet + CARTO tiles |

---

Built for the Microsoft Fabric Hackathon 🏆
