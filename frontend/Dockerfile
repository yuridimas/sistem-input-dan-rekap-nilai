# Image development Vite pada profile local Compose dengan sumber yang dapat di-mount.
# Build produksi memakai Dockerfile.prod agar aset statis dilayani oleh Nginx.
FROM node:24

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
