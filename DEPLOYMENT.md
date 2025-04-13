# Deployment Guide for Vibe Todo

This document provides detailed deployment instructions for the Vibe Todo application in various environments.

## Docker Deployment (Recommended)

### Prerequisites
- Docker
- Docker Compose

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/copyleftdev/vibe-todo.git
   cd vibe-todo
   ```

2. **Build the Docker image**
   ```bash
   docker-compose build
   ```

3. **Run the application**
   ```bash
   docker-compose run app
   ```

4. **Production Considerations**
   - Set up a persistent volume for the SQLite database
   ```yaml
   # In docker-compose.yml
   volumes:
     - ./data:/app/data
   ```
   - Configure logging to external services
   - Set up a health check endpoint

## Manual Deployment

### Prerequisites
- Python 3.11+
- SQLite3

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/copyleftdev/vibe-todo.git
   cd vibe-todo
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python -m todo
   ```

5. **Production Considerations**
   - Use a process manager like supervisord or systemd
   - Set up regular database backups
   - Configure logging to files or external services

## Deployment as a Service

### Using Systemd (Linux)

1. **Create a systemd service file**
   ```bash
   sudo nano /etc/systemd/system/vibe-todo.service
   ```

2. **Add the following configuration**
   ```
   [Unit]
   Description=Vibe Todo Application
   After=network.target

   [Service]
   User=copyleftdev
   WorkingDirectory=/path/to/vibe-todo
   ExecStart=/path/to/vibe-todo/venv/bin/python -m todo
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service**
   ```bash
   sudo systemctl enable vibe-todo
   sudo systemctl start vibe-todo
   ```

4. **Check service status**
   ```bash
   sudo systemctl status vibe-todo
   ```

## Monitoring and Logging

### Monitoring
- The application outputs structured JSON logs
- These can be ingested by ELK Stack, Prometheus, or similar tools
- Set up alerts for SLA violations (operations exceeding 10ms)

### Key Metrics to Monitor
- Operation latency (SLA threshold is 10ms)
- Error rates
- Database size and performance

## Backup Strategy

### SQLite Database Backup
```bash
# Copy the SQLite database file
cp /path/to/vibe-todo/todo.db /path/to/backup/todo.db.$(date +%Y%m%d)

# Or use the SQLite backup command
sqlite3 /path/to/vibe-todo/todo.db ".backup /path/to/backup/todo.db.$(date +%Y%m%d)"
```

## Troubleshooting

### Common Issues

1. **Database locked errors**
   - Ensure no other processes are accessing the database
   - Check file permissions

2. **Performance degradation**
   - Run the benchmark tests to verify SLA compliance
   - Check for database fragmentation
   - Consider running VACUUM command on the SQLite database

3. **High error rates**
   - Check the logs for input validation errors
   - Run the evolutionary tests to identify potential issues

## Version Upgrades

When upgrading to a new version:

1. **Backup your database**
2. **Check release notes for breaking changes**
3. **Run all tests against your data before deploying**
   ```bash
   python run_all_tests.py --evolutionary
   ```
4. **Consider running tests against a copy of your production database**

## Security Considerations

- Regularly update dependencies
- Run security scans on your code
- Implement rate limiting if exposed to public networks
- Consider data encryption at rest for sensitive tasks
