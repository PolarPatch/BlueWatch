FROM python:3.12-slim

# Install system dependencies for Bluetooth
RUN apt-get update && apt-get install -y --no-install-recommends \
    bluez \
    libglib2.0-dev \
    libdbus-1-dev \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (but we'll need bluetooth group access)
RUN useradd -m -s /bin/bash bluewatch && \
    usermod -aG bluetooth bluewatch

WORKDIR /app

# Copy and install Python dependencies
COPY pyproject.toml .
COPY bluewatch/ bluewatch/
COPY README.md .

RUN pip install --no-cache-dir -e ".[metrics]"

# Create data directory for database and cache
RUN mkdir -p /data && chown bluewatch:bluewatch /data

# Bundle MAC vendor database at build time as fallback
RUN python -c "from mac_vendor_lookup import MacLookup; MacLookup().update_vendors()" \
    && cp /root/.cache/mac-vendors.txt /data/mac-vendors.txt \
    && chown bluewatch:bluewatch /data/mac-vendors.txt \
    || echo "Warning: could not bundle vendor DB"

# Environment variables
ENV BLUEWATCH_DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

# Expose web dashboard and metrics ports
EXPOSE 8080
EXPOSE 9199

# Entrypoint handles PUID/PGID user switching
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "bluewatch.daemon"]
