FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Expose Vite default port
EXPOSE 5173

# Start Vite server (configured to bind to 0.0.0.0 via command)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
