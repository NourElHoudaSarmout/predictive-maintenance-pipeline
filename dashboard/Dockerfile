FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ENV VITE_API_URL=http://localhost:5000
RUN npm run build
 
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
