# HoriZonix Backend Deployment Guide for Render

This guide will help you deploy the HoriZonix Django backend to Render.

## 🚀 Quick Deployment Steps

### 1. Prepare Your Repository
Make sure all files are committed to your Git repository:
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Deploy on Render

#### Option A: Using render.yaml (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to deploy

#### Option B: Manual Configuration
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the following settings:
   - **Name**: `horizonix-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn main.wsgi:application`

### 3. Environment Variables

Set these environment variables in your Render dashboard:

#### Required Variables:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ENVIRONMENT=production
```

#### Database (NeonDB):
```
NEON_HOST=ep-patient-lake-a168r1pr-pooler.ap-southeast-1.aws.neon.tech
NEON_DATABASE=neondb
NEON_USER=neondb_owner
NEON_PASSWORD=npg_jaJ1HEqzy7VP
NEON_PORT=5432
```

#### Email Configuration:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
```

#### Frontend URL:
```
FRONTEND_URL=https://your-frontend-domain.vercel.app
```

#### Optional (Cloudinary):
```
CLOUDINARY_URL=your-cloudinary-url
```

### 4. Custom Domain (Optional)

1. In your Render service settings
2. Go to "Settings" → "Custom Domains"
3. Add your custom domain
4. Update DNS records as instructed

## 🔧 Configuration Files

### render.yaml
- Contains all deployment configuration
- Automatically configures environment variables
- Sets up build and start commands

### build.sh
- Custom build script for Render
- Installs dependencies
- Collects static files
- Runs database migrations

### Procfile
- Defines how to start the application
- Uses Gunicorn WSGI server

## 🛠️ Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check Python version (3.12.0)
   - Verify all dependencies in requirements.txt
   - Check build logs in Render dashboard

2. **Database Connection Issues**:
   - Verify NeonDB credentials
   - Check if database is accessible
   - Ensure SSL is enabled

3. **Static Files Not Loading**:
   - Run `python manage.py collectstatic --noinput`
   - Check STATIC_ROOT setting
   - Verify WhiteNoise configuration

4. **CORS Issues**:
   - Update CORS_ALLOWED_ORIGINS
   - Add your frontend domain
   - Check CSRF_TRUSTED_ORIGINS

### Debugging:

1. **Check Logs**:
   - Go to Render dashboard
   - Click on your service
   - Go to "Logs" tab

2. **Environment Variables**:
   - Verify all required variables are set
   - Check for typos in variable names

3. **Database**:
   - Test connection locally first
   - Check NeonDB dashboard

## 📊 Monitoring

### Health Check:
Your app includes a health check endpoint:
```
GET https://your-app.onrender.com/api/auth/health/
```

### Performance:
- Render provides basic monitoring
- Check response times in logs
- Monitor database performance in NeonDB

## 🔒 Security

### Production Security:
- DEBUG=False in production
- SECRET_KEY is auto-generated
- CORS is properly configured
- CSRF protection enabled
- Secure cookie settings

### Environment Variables:
- Never commit sensitive data
- Use Render's environment variable system
- Rotate secrets regularly

## 🚀 Post-Deployment

### 1. Test Your API:
```bash
curl https://your-app.onrender.com/api/auth/health/
```

### 2. Update Frontend:
Update your frontend's API base URL to:
```
https://your-app.onrender.com
```

### 3. Monitor:
- Check Render dashboard regularly
- Monitor logs for errors
- Set up alerts if needed

## 📝 Notes

- Render free tier has limitations (sleeps after 15 minutes of inactivity)
- Consider upgrading to paid plan for production
- Database is hosted on NeonDB (separate service)
- Static files are served by WhiteNoise
- Email service requires Gmail app password

## 🆘 Support

If you encounter issues:
1. Check Render documentation
2. Review Django deployment guides
3. Check your application logs
4. Verify all environment variables

Happy deploying! 🎉
