# AI Tasks Manager

An AI-powered task management app built with FastAPI and React.  
Users can create tasks manually, upload photos to extract task text, and get AI-suggested priority and deadlines.

## Features

- User registration and login with JWT.
- Create, edit, delete, and list tasks.
- Upload a photo and convert it into a task.
- AI-powered priority classification.
- AI-powered deadline suggestions.
- PostgreSQL database support.
- React frontend with a simple task UI.

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT authentication
- OpenAI API

### Frontend
- React
- TypeScript
- Vite
- CSS

## Project Structure

```txt
tasks-app/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── tasks.py
│   ├── models.py
│   ├── schemas.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── components/
│   │       ├── Login.tsx
│   │       └── TaskList.tsx
│   └── vite.config.ts
├── API_DOCS.md
└── README.md
