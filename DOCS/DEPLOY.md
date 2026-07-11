# Checklist de despliegue

Los archivos de configuración ya están listos en el repo (`Dockerfile`, `render.yaml`, `frontend/vercel.json`). Faltan pasos que requieren tu cuenta (GitHub/Render/Vercel), así que no los puedo hacer yo — aquí está el paso a paso.

## 1. Subir el repo a GitHub (debe quedar público)

```bash
git add -A
git commit -m "Scaffold inicial: backend FastAPI + LangGraph, frontend React, HU1 Radar"
gh repo create track5-marketmind --public --source=. --remote=origin --push
# o crea el repo manualmente en github.com y luego:
# git remote add origin <url> && git push -u origin main
```

## 2. Backend en Render

1. Entra a https://dashboard.render.com → **New +** → **Web Service**.
2. Conecta tu cuenta de GitHub y selecciona este repo.
3. Render debería detectar `render.yaml` automáticamente (Blueprint). Si no, configura a mano:
   - **Runtime:** Docker (usa el `Dockerfile` de la raíz).
   - **Plan:** Free.
4. En **Environment**, agrega `GOOGLE_API_KEY` con tu key (la del `.env` local, nunca la subas al repo).
5. Deploy. Copia la URL pública que te da Render (algo como `https://track5-backend.onrender.com`).

## 3. Frontend en Vercel

1. Entra a https://vercel.com/new → importa el mismo repo de GitHub.
2. **Root Directory:** `frontend`.
3. Framework preset: Vite (debería autodetectarse).
4. En **Environment Variables**, agrega `VITE_API_URL` = la URL del backend en Render (paso 2).
5. Deploy. Copia la URL pública (`https://track5-marketmind.vercel.app` o similar).

## 4. Actualizar CORS del backend

En Render, edita la variable `CORS_ORIGINS` del backend para que incluya la URL real de Vercel (por ahora está en `*` para no bloquear mientras se prueba, pero antes de la entrega final conviene restringirla a la URL exacta del frontend).

## 5. Verificar

Abre la URL de Vercel en el navegador y repite el recorrido de las 3 páginas (Radar, AI Analysis, Briefings) — debe verse igual que en local. Ese es el **link de despliegue** para el entregable #5.

## Migrar a otro host (si un compañero consigue uno de pago)

El `Dockerfile` es portable: cualquier plataforma que soporte "deploy from Dockerfile" (Railway, Fly.io, un VPS, etc.) sirve sin cambiar código — solo apunta el nuevo servicio al mismo `Dockerfile` y copia las mismas variables de entorno.
