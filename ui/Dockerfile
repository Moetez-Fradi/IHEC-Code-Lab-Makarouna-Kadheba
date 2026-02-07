# Use Node 20 Alpine
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application (for production)
# RUN npm run build

# Expose port
EXPOSE 3000

# Run in development mode
CMD ["npm", "run", "dev"]
