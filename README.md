# Adaptive Variable-Resolution 2.5D LiDAR Mapping for Dynamic Environment Perception

An engineering research prototype and demonstration workstation for semantic-aware variable-resolution 2.5D elevation and occupancy grid mapping from Velodyne HDL-64E LiDAR scans.

---

## 1. System Architecture

```
LiDAR Scan (.bin)
       ↓
Preprocessing & Filtering (Range + ROI + Downsampling)
       ↓
AI Perception: RandLA-Net Semantic Segmentation
       ↓
Perception Contract: Points + 8 Semantic Labels + Confidence Scores
       ↓
Multi-Criteria Importance & Frame-to-Frame Movement Estimation
       ↓
Spatial Discretization:
  ├─ Fixed-Resolution Uniform Grid (Baseline)
  └─ Adaptive Variable-Resolution Grid (Coarse Base + Fine Subdivided Cells)
       ↓
Comparative Efficiency Metrics (Cell Savings, Analytical Memory Reduction)
       ↓
FastAPI REST Service Layer (JSON API)
       ↓
Streamlit + Plotly Engineering Workstation Dashboard
```

---

## 2. 8-Class Project Taxonomy

| ID | Class Name | Priority | Recommended Cell Resolution | Color Code |
|:---:|---|---|:---:|:---:|
| **0** | `road` | Ground Base | Coarse ($0.40\,\text{m}$) | `#7f3f7f` |
| **1** | `sidewalk` | Boundary | Medium ($0.20\,\text{m}$) | `#f42396` |
| **2** | `building` | Static Barrier | Coarse ($0.50\,\text{m}$) | `#595959` |
| **3** | `vegetation` | Soft Obstacle | Medium ($0.30\,\text{m}$) | `#389938` |
| **4** | `vehicle` | Dynamic Critical | Fine ($0.10\,\text{m}$) | `#337fe5` |
| **5** | `pedestrian` | Ultra-Critical | Ultra-Fine ($0.05\,\text{m}$) | `#e52626` |
| **6** | `pole_sign` | Vertical Obstacle | Fine ($0.10\,\text{m}$) | `#ffd819` |
| **7** | `other` | Noise / Background | Default ($0.40\,\text{m}$) | `#a5a5a5` |

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.13)
- PyTorch 2.0+

### Clone & Install Dependencies
```bash
git clone https://github.com/sumanisfr/2.5D-Lidar-Mapping-for-Dynamic-Environment-Perception.git
cd 2.5D-Lidar-Mapping-for-Dynamic-Environment-Perception

pip install -r requirements.txt
```

---

## 4. Running the System

### Option A: Unified Launcher (Recommended)
Launches the FastAPI backend daemon and opens the Streamlit engineering workstation:
```bash
python run_dashboard.py
```

### Option B: Individual Components
**Start FastAPI Backend:**
```bash
uvicorn src.backend.app:app --host 127.0.0.1 --port 8000
```
API Documentation available at: `http://127.0.0.1:8000/docs`

**Start Streamlit Frontend Dashboard:**
```bash
python -m streamlit run src/frontend/app.py --server.port 8501
```
Workstation available at: `http://localhost:8501`

---

## 5. API Reference Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health, compute device (CPU/CUDA), checkpoint status |
| `GET` | `/api/v1/classes` | Canonical 8-class taxonomy, colors, recommended cell resolutions |
| `GET` | `/api/v1/samples` | Discovers available `.bin` LiDAR scans in data directories |
| `GET` | `/api/v1/samples/{id}` | Scan metadata for a specific frame |
| `POST` | `/api/v1/inference` | Executes RandLA-Net semantic segmentation forward pass |
| `POST` | `/api/v1/map/uniform` | Generates fixed-resolution 2.5D grid map |
| `POST` | `/api/v1/map/adaptive` | Generates adaptive variable-resolution 2.5D grid map |
| `POST` | `/api/v1/map/compare` | Computes cell reduction % and memory comparison benchmarks |

---

## 6. Frontend Dashboard Modules

1. **Dashboard**: Executive overview containing the 3D LiDAR viewer, live 8-class legend, 2.5D semantic top view, elevation profile, circular KPI gauges, and system activity logs.
2. **Point Cloud Viewer**: Full-screen interactive 3D WebGL inspection with Semantic, Elevation (Z), Intensity, and Error Map color modes; 3D/BEV/Side camera presets; class and confidence filters.
3. **2.5D Mapping**: Side-by-side comparison of fixed uniform grids vs coarse-to-fine adaptive grids, colorable by resolution level, elevation, semantic class, or importance.
4. **Semantic View**: Quantitative class distributions, confidence statistics, and ground-truth evaluation metrics.
5. **Terrain Analysis**: Longitudinal and lateral elevation profiles, height variance, continuous cell elevation statistics.
6. **Object Analysis**: Explicit technical distinction between point-wise semantic counts and candidate 3D spatial clusters (DBSCAN) with bounding box dimensions.
7. **Performance**: Empirical latency breakdown by pipeline stage, computed FPS, point throughput, and analytical struct memory model.
8. **Settings & Diagnostics**: Backend health monitoring, hardware platform inspection, and raw JSON diagnostic viewers.

---

## 7. Running Tests

Execute the complete 94-test automated test suite:
```bash
python -m pytest tests/ -v
```

Module-specific test commands:
```bash
# Mapping & adaptive grid algorithms
python -m pytest tests/test_mapping -q

# Backend API routes and services
python -m pytest tests/test_backend -q

# AI perception & label synchronization
python -m pytest tests/test_ai_data_pipeline.py -q

# Frontend API client & data adapter
python -m pytest tests/test_frontend_api_client.py -q
```

---

## 8. Known Prototype Limitations

- **Baseline Checkpoint**: The current RandLA-Net checkpoint was trained for 1 epoch on limited data as a baseline prototype. Predictions are noisy and should not be presented as production perception models.
- **Movement Estimation**: Point displacement uses nearest-neighbor spatial queries via `scipy.spatial.cKDTree` rather than full SLAM ego-motion compensation or scene flow.
- **Memory Metric**: Memory reduction figures reflect a 64-byte theoretical struct model per cell; actual runtime heap depends on Python dict/NumPy allocation overhead.
- **2.5D Representation**: A 2.5D grid stores one elevation profile per horizontal cell $(x, y)$, meaning multi-level overhanging structures (such as bridges or tunnel ceilings) are projected onto the dominant surface.

## 9. Production Deployment with Docker

The repository includes a production Docker Compose deployment. It runs the FastAPI inference service privately and serves the built React dashboard through Nginx on port 80.

### Requirements

- Docker Engine and Docker Compose v2 on a Linux server or Docker Desktop
- The `checkpoints/` directory with a model checkpoint
- The `data/` directory with the LiDAR samples used by the dashboard

### Start the application

```bash
docker compose up -d --build
```

Open `http://localhost` for the dashboard. The API documentation is available at `http://localhost/docs`.

### Configure inference hardware

The default configuration uses CPU inference. To use a CUDA-enabled backend, create a `.env` file beside `docker-compose.yml`:

```env
LIDAR_DEVICE=cuda
```

The backend container needs a CUDA-enabled Docker runtime and compatible PyTorch image for GPU inference; CPU mode works with the included Python image without additional runtime configuration.

### Update or stop the deployment

```bash
docker compose up -d --build
docker compose logs -f backend
docker compose down
```

For a public server, place HTTPS in front of port 80 using a cloud load balancer or Nginx/Caddy on the host. Do not expose the backend port directly; the frontend container proxies `/api/` to FastAPI internally.
