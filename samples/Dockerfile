# RISKY Dockerfile for AI Testing

# 🔴 Vulnerability: Using 'latest' tag instead of a specific version
FROM ubuntu:latest

# 🔴 Vulnerability: Running as root user (default)
# No USER instruction provided

# 🟠 Hardcoded Secrets (Static Analysis should catch this)
ENV API_KEY="sk-1234567890abcdef1234567890abcdef"
ENV DB_PASSWORD="very-secure-password"

# 🔴 Security risk: Installing unnecessary packages
RUN apt-get update && apt-get install -y \
    curl \
    netcat \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 🟢 Best practice (missing): HEALTHCHECK

EXPOSE 8080
CMD ["./server"]
