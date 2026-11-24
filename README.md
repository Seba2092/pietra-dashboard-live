# Joyería Pietra · Dashboard Live (Meta Ads + Google Ads + IG/FB)

Actualiza automáticamente las métricas de **Meta Ads**, **Google Ads** (vía Google Sheet alimentado por Google Ads Scripts) e **Instagram/Facebook Orgánico** y publica `dist/index.html` sin depender de IA ni servidores pagos.

## Puesta en producción en GitHub Pages (5 minutos)

1. **Crear un repositorio en GitHub** (ej. `pietra-dashboard-live`).
   - *Nota:* GitHub Pages gratis requiere repositorio público (o GitHub Pro para repo privado). Como `.env` y `data/*.json` están ignorados en `.gitignore`, tu token jamás se sube al repo; si querés que el link del dashboard no sea público, podés conectar este mismo repo a **Netlify** o **Vercel** con protección por contraseña.
2. **Subir los archivos de esta carpeta** al repositorio (`git init`, `git add .`, `git commit -m "Initial live dashboard"`, `git push`).
3. **Cargar los 2 Secrets** en GitHub → *Settings → Secrets and variables → Actions → New repository secret*:
   - `META_ACCESS_TOKEN`: tu token permanente del System User `Reportes Pietra`.
   - `GOOGLE_SHEET_ID`: `1nRWkUGnENJzFJDowZQDinW1aMvCT7rbFYKKEJ_ud9fw`
4. **Activar GitHub Pages** en *Settings → Pages → Source:* elegí **GitHub Actions**.
5. **Primera corrida manual:** Andá a la pestaña **Actions → Actualizar Dashboard Pietra → Run workflow**. En ~20 segundos te aparece la URL fija `https://<tu-usuario>.github.io/pietra-dashboard-live/` que se actualizará sola todos los días a las **08:00 AM (hora Argentina)**.
