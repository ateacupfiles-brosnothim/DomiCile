# Domicile — Global House Hunting App

AI-powered property search for any city worldwide.

## Deploy to Vercel (free, 2 minutes)

1. Push this repo to GitHub
2. Go to vercel.com → New Project → Import your repo
3. In **Environment Variables**, add:
   - `GEMINI_API_KEY` = your key from [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
4. Click Deploy

That's it. No server, no database, no costs.

## How it works

- `public/index.html` — the entire frontend (HTML/CSS/JS, no framework)
- `api/search.js` — Vercel Edge Function that proxies all AI calls to Gemini 2.0 Flash
- The Gemini API key never touches the browser

## Free tier limits

- Gemini 2.0 Flash: **1,500 requests/day**, resets midnight Pacific
- Vercel: **100GB bandwidth/month**, unlimited deployments
- Both are free with no credit card required

## Agents integrated

| Agent | Role |
|---|---|
| Gemini 2.0 Flash | Search, Sentiment, Neighborhood scores |
| Kimi (regex engine) | PDF listing analyzer (client-side) |
| Copilot (formula) | Excel export scoring |
