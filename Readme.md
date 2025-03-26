# Cài đặt HTTPS cho FastAPI Service với Traefik

Hướng dẫn này mô tả cách thiết lập HTTPS cho FastAPI service sử dụng Traefik làm reverse proxy, với self-signed certificate.

## Yêu cầu

- Docker và Docker Compose đã được cài đặt
- VPS hoặc máy chủ có IP công khai
- Ports 80, 443, 8080 và 4000 đã được mở trong firewall

## Các bước cài đặt

### 1. Tạo thư mục và certificate

```bash
# Tạo thư mục cần thiết
mkdir -p certs traefik-config

# Tạo self-signed certificate
cd certs
openssl genrsa -out server.key 2048
openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=YOUR_SERVER_IP"
# Thay YOUR_SERVER_IP bằng IP thực tế của VPS
```

### 2. Cấu hình Traefik TLS

Tạo file `traefik-config/tls.yml`:

```yaml
tls:
  certificates:
    - certFile: /certs/server.crt
      keyFile: /certs/server.key
```

### 3. Cấu hình Docker Compose

Tạo file `docker-compose.yml` với nội dung như sau:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--providers.file.directory=/certs"
      - "--providers.file.watch=true"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./certs:/certs
      - ./traefik-config:/traefik-config
    networks:
      - app-network
    restart: unless-stopped

  app-service:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: app-service
    environment:
      - SERVICE_HOST=service-name
      - SERVICE_PORT=8001
      - DB_URL=postgresql+psycopg2://username:password@db-host:5432/database_name
      - ROOT_PATH=/api-endpoint  # Biến môi trường cho FastAPI root_path
    ports:
      - "4000:4000"  # Port truy cập trực tiếp
    volumes:
      - ./app:/app
    networks:
      - app-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app-service.rule=PathPrefix(`/api-endpoint`)"
      - "traefik.http.routers.app-service.entrypoints=websecure"
      - "traefik.http.routers.app-service.tls=true"
      - "traefik.http.services.app-service.loadbalancer.server.port=4000"
      - "traefik.http.routers.app-service-http.rule=PathPrefix(`/api-endpoint`)"
      - "traefik.http.routers.app-service-http.entrypoints=web"
      - "traefik.http.routers.app-service-http.middlewares=redirect-to-https"
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
      - "traefik.http.middlewares.app-service-strip.stripprefix.prefixes=/api-endpoint"
      - "traefik.http.routers.app-service.middlewares=app-service-strip"

networks:
  app-network:
    driver: bridge
```

### 4. Cấu hình FastAPI để sử dụng root_path

Cập nhật file main.py của ứng dụng FastAPI để sử dụng biến môi trường ROOT_PATH:

```python
import os
from fastapi import FastAPI

# Lấy đường dẫn cơ sở từ biến môi trường
root_path = os.getenv("ROOT_PATH", "")

# Cấu hình FastAPI
app = FastAPI(
    title="API Service",
    description="API for data processing",
    version="1.0.0",
    root_path=root_path,  # Sử dụng root_path
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Routes của bạn...
```

### 5. Khởi động dịch vụ

```bash
docker-compose up -d
```

### 6. Kiểm tra trạng thái

```bash
docker-compose ps
```

## Cách truy cập dịch vụ

- **FastAPI Service (HTTPS)**: `https://YOUR_SERVER_IP/api-endpoint`
- **FastAPI Swagger UI**: `https://YOUR_SERVER_IP/api-endpoint/docs`
- **FastAPI Trực tiếp (HTTP)**: `http://YOUR_SERVER_IP:4000`
- **Traefik Dashboard**: `http://YOUR_SERVER_IP:8080`

## Giải thích cấu hình Traefik

### Labels

- `traefik.enable=true`: Kích hoạt Traefik cho service này
- `traefik.http.routers.app-service.rule=PathPrefix(/api-endpoint)`: Định nghĩa đường dẫn API
- `traefik.http.routers.app-service.entrypoints=websecure`: Sử dụng entrypoint 443 (HTTPS)
- `traefik.http.routers.app-service.tls=true`: Kích hoạt TLS (HTTPS)
- `traefik.http.services.app-service.loadbalancer.server.port=4000`: Port nội bộ của service
- `traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https`: Chuyển hướng HTTP sang HTTPS
- `traefik.http.middlewares.app-service-strip.stripprefix.prefixes=/api-endpoint`: Loại bỏ prefix trước khi chuyển tiếp request

## Cấu hình Swagger UI

Để Swagger UI hoạt động đúng khi truy cập thông qua Traefik, cần đảm bảo hai điều:

1. **Biến môi trường ROOT_PATH**: Thêm `ROOT_PATH=/api-endpoint` trong cấu hình environment của service
2. **FastAPI config với root_path**: Cấu hình FastAPI với root_path để xử lý đường dẫn đúng

Nếu Swagger UI vẫn gặp lỗi "Failed to load API definition", có thể thêm cấu hình OpenAPI server URL tuyệt đối:

```python
@app.on_event("startup")
async def startup_event():
    app.openapi_schema = None  # Clear cached schema
    
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = app.openapi()
    # Đặt server URL tuyệt đối
    openapi_schema["servers"] = [
        {"url": f"https://YOUR_SERVER_IP/api-endpoint"}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

## Lưu ý

- **Self-signed Certificate**: Trình duyệt sẽ hiển thị cảnh báo bảo mật vì certificate tự ký
- **ROOT_PATH và Middleware**: Cần đảm bảo ROOT_PATH trong FastAPI khớp với đường dẫn trong cấu hình Traefik

## Khắc phục sự cố

### Port đã được sử dụng

Nếu gặp lỗi "port is already allocated", kiểm tra các port đang được sử dụng:

```bash
sudo netstat -tulpn | grep -E ':(80|443|8080|4000)'
```

### Kiểm tra logs

```bash
docker-compose logs traefik
docker-compose logs app-service
```

### Swagger UI không hoạt động

Nếu Swagger UI không tải được API definition:

1. Kiểm tra xem endpoint `/api-endpoint/openapi.json` có hoạt động không
2. Đảm bảo ROOT_PATH trong FastAPI khớp với đường dẫn trong Traefik
3. Kiểm tra browser console để xem có lỗi CORS hoặc lỗi network không

## Tùy chỉnh

Để thay đổi đường dẫn API (hiện tại là `/api-endpoint`), hãy cập nhật:
1. Biến môi trường `ROOT_PATH` trong environment
2. Các label Traefik có chứa đường dẫn `/api-endpoint`

---

Tài liệu này cung cấp cách triển khai HTTPS cho FastAPI service sử dụng Traefik, phù hợp cho môi trường phát triển. Cho production, nên sử dụng Let's Encrypt với domain thực.