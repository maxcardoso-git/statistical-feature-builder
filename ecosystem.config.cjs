module.exports = {
  apps: [
    {
      name: 'sfb-service',
      script: '/var/www/SFB/venv/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: '/var/www/SFB',
      instances: 1,
      exec_mode: 'fork',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
        PATH: '/var/www/SFB/venv/bin:' + process.env.PATH
      },
      error_file: '/var/log/pm2/sfb-error.log',
      out_file: '/var/log/pm2/sfb-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    }
  ]
};
