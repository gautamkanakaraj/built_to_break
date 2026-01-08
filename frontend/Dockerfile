FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

# Expose port 3000 as per requirements
EXPOSE 3000

ENV PORT=3000
ENV BACKEND_URL=http://backend:4000

CMD ["npm", "start"]
