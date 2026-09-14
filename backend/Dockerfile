FROM python:3.11-bullseye

# System deps + Node.js 20 + yarn
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libstdc++6 curl build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install --no-binary greenlet "greenlet>=3.1.1,<4.0.0"
RUN pip install -r backend/requirements.txt
RUN pip install emergentintegrations==0.2.0 --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Frontend (CRA) — yarn obligatoire (bug ajv codegen avec npm)
# REACT_APP_BACKEND_URL laissé vide : le backend sert le SPA sur la même origine,
# donc les appels API relatifs (/api) fonctionnent quel que soit le domaine (Railway ou custom).
RUN cd frontend && yarn install --network-timeout 600000
RUN cd frontend && VITE_API_URL= VITE_SAAS_URL=https://app.zayado.net VITE_WP_URL=https://cms.zayado.net yarn build
RUN mkdir -p backend/static && cp -r frontend/dist/* backend/static/

EXPOSE $PORT

CMD cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
