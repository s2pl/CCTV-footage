# 📹 CCTV Management System - User Guide

## Welcome to Your Security Camera System! 🎥

This guide will help you understand and use your CCTV management system like a professional, even if you're just starting out. We'll explain everything in simple terms that anyone can understand.

---

## 📋 Table of Contents

1. [What is This System?](#what-is-this-system)
2. [Getting Started](#getting-started)
3. [Setting Up Your Cameras](#setting-up-your-cameras)
4. [Connecting Cameras with Tailscale](#connecting-cameras-with-tailscale)
5. [Using the Dashboard](#using-the-dashboard)
6. [Live Feed Viewing](#live-feed-viewing)
7. [Recording Management](#recording-management)
8. [User Management](#user-management)
9. [Scheduling Recordings](#scheduling-recordings)
10. [Troubleshooting](#troubleshooting)

---

## What is This System? 🏠

Your CCTV Management System is like having a smart security guard that never sleeps! It helps you:

- **Watch your cameras live** from anywhere in the world
- **Record important moments** automatically or manually
- **Manage who can see what** with user permissions
- **Schedule recordings** for specific times
- **Access everything remotely** through the internet

Think of it as your personal security command center! 🛡️

---

## Getting Started 🚀

### Step 1: Logging In
1. Open your web browser
2. Go to your CCTV system website
3. Enter your username and password
4. Click "Login"

**First time?** Ask your system administrator for your login details.

### Step 2: Understanding the Interface
Once logged in, you'll see:
- **Sidebar** (left side): Navigation menu
- **Main area**: Where all the action happens
- **Header** (top): Quick access buttons

---

## Setting Up Your Cameras 📷

### Adding a New Camera

1. **Go to "Cameras"** in the sidebar
2. **Click "Add Camera"** button
3. **Fill in the details:**
   - **Camera Name**: Give it a friendly name (e.g., "Front Door Camera")
   - **IP Address**: The camera's network address
   - **Username & Password**: Camera login credentials
   - **RTSP URL**: The streaming address (usually auto-generated)

### Camera Information Explained

- **IP Address**: Like a home address for your camera on the network
- **RTSP URL**: The "channel" where your camera sends video
- **Username/Password**: Keys to access your camera

### Testing Your Camera
- Click "Test Connection" to make sure everything works
- Green status = Good to go! ✅
- Red status = Check your settings ❌

---

## Connecting Cameras with Tailscale 🌐

Tailscale helps you access your cameras from anywhere in the world, even when you're not at home!

### What is Tailscale?
Tailscale is like a magic tunnel that connects all your devices securely, no matter where they are in the world.

### Setting Up Tailscale for Your Cameras

#### For a Single Camera (Specific IP):
```bash
tailscale up --accept-routes --advertise-routes=192.168.0.102/32
```

**What this means:**
- `192.168.0.102` = Your camera's IP address
- `/32` = Only this exact camera
- This makes ONLY this camera accessible from anywhere

#### For Multiple Cameras (IP Range):
```bash
tailscale up --accept-routes --advertise-routes=192.168.1.0/24
```

**What this means:**
- `192.168.1.0/24` = All cameras in the 192.168.1.x range
- This makes ALL cameras in this range accessible
- **Important**: This won't work with 192.168.0.x range!

### Step-by-Step Tailscale Setup:

1. **Install Tailscale** on your computer/server
2. **Run the command** (choose single camera or range)
3. **Wait for connection** (usually takes 30 seconds)
4. **Test access** by trying to view cameras from another location

### Why Use Tailscale?
- **Secure**: Your cameras are protected
- **Easy**: No complex network setup needed
- **Reliable**: Works from anywhere with internet
- **Free**: For personal use

---

## Using the Dashboard 📊

The Dashboard is your command center! Here you can see:

### System Overview
- **Total Cameras**: How many cameras you have
- **Online Cameras**: How many are working right now
- **Recent Activity**: What's been happening
- **System Status**: Everything working properly?

### Quick Actions
- **View All Cameras**: See all your cameras at once
- **Start Recording**: Begin recording on any camera
- **Check Status**: See if everything is working

---

## Live Feed Viewing 👀

### Viewing Live Feeds

1. **Click "Live Feed"** in the sidebar
2. **Choose your view:**
   - **Grid View**: See multiple cameras at once (2x2, 3x3, 4x4)
   - **Single View**: Focus on one camera in detail

### Live Feed Controls

- **🔴 Record Button**: Start/stop recording
- **🔊 Audio**: Mute/unmute sound
- **📐 Quality**: Switch between high/low quality
- **🔄 Refresh**: Restart if stream stops working
- **⏸️ Pause**: Pause the live feed

### Camera Status Indicators
- **🟢 Green**: Camera is online and working
- **🔴 Red**: Camera is offline or has problems
- **🟡 Yellow**: Camera is connecting or has issues

---

## Recording Management 📹

### Manual Recording
1. **Go to Live Feed**
2. **Click the record button** on any camera
3. **Set duration** (how long to record)
4. **Click "Start Recording"**

### Automatic Recording
- **Scheduled**: Record at specific times
- **Motion Detection**: Record when something moves
- **Continuous**: Record 24/7

### Viewing Recordings
1. **Click "Recordings"** in the sidebar
2. **Filter by:**
   - Date range
   - Camera
   - Recording type
3. **Click on any recording** to watch it
4. **Download** if you need to save it

---

## User Management 👥

### Adding New Users
1. **Go to "Users"** in the sidebar
2. **Click "Add User"**
3. **Fill in details:**
   - Name and email
   - Username and password
   - Role (what they can do)

### User Roles Explained
- **Admin**: Can do everything
- **Operator**: Can view and control cameras
- **Viewer**: Can only watch, cannot control

### Managing Permissions
- **Camera Access**: Which cameras each user can see
- **Recording Rights**: Who can start/stop recordings
- **Schedule Access**: Who can create schedules

---

## Scheduling Recordings ⏰

### Creating a Schedule
1. **Go to "Schedule"** in the sidebar
2. **Click "New Schedule"**
3. **Choose schedule type:**
   - **One-time**: Record at a specific date/time
   - **Daily**: Record at the same time every day
   - **Weekly**: Record on specific days
   - **Continuous**: Record 24/7

### Schedule Options
- **Start Time**: When to begin recording
- **Duration**: How long to record
- **Cameras**: Which cameras to include
- **Quality**: Recording quality level

### Managing Schedules
- **View all schedules** in the schedule list
- **Edit** any schedule by clicking on it
- **Delete** schedules you no longer need
- **Enable/Disable** schedules without deleting them

---

## Troubleshooting 🔧

### Common Problems and Solutions

#### Camera Won't Connect
**Problem**: Camera shows as offline
**Solutions**:
1. Check if camera is plugged in and powered on
2. Verify the IP address is correct
3. Check username and password
4. Test network connection

#### Can't See Live Feed
**Problem**: Video won't load
**Solutions**:
1. Refresh the page
2. Check internet connection
3. Try a different browser
4. Restart the camera

#### Recording Not Working
**Problem**: Can't start recording
**Solutions**:
1. Check if camera is online
2. Verify storage space
3. Check recording permissions
4. Restart the application

#### Tailscale Connection Issues
**Problem**: Can't access cameras remotely
**Solutions**:
1. Check Tailscale status: `tailscale status`
2. Verify the IP range is correct
3. Make sure Tailscale is running
4. Check firewall settings

### Getting Help
- **Check the logs** in the system
- **Contact your administrator** for technical issues
- **Restart the system** if nothing else works

---

## Best Practices 💡

### Security Tips
- **Change default passwords** on all cameras
- **Use strong passwords** for user accounts
- **Regularly update** the system
- **Monitor access logs** for suspicious activity

### Performance Tips
- **Don't run too many streams** at once
- **Use appropriate quality settings** for your internet speed
- **Regularly clean up** old recordings
- **Monitor storage space**

### Maintenance
- **Check camera status** regularly
- **Clean camera lenses** for better video quality
- **Update firmware** when available
- **Backup important recordings**

---

## Quick Reference Card 📋

### Essential Buttons
- **Dashboard**: System overview
- **Cameras**: Manage your cameras
- **Live Feed**: Watch live video
- **Recordings**: View saved videos
- **Users**: Manage user accounts
- **Schedule**: Set up automatic recording
- **Settings**: Configure the system

### Emergency Procedures
1. **Camera offline**: Check power and network
2. **Can't login**: Contact administrator
3. **System slow**: Restart the application
4. **Lost recordings**: Check storage and permissions

---

## Conclusion 🎯

Congratulations! You now know how to use your CCTV Management System like a professional. Remember:

- **Start simple**: Get comfortable with basic features first
- **Ask questions**: Don't hesitate to ask for help
- **Practice regularly**: The more you use it, the easier it gets
- **Stay secure**: Always use strong passwords and permissions

Your security system is now ready to protect what matters most to you! 🛡️✨

---

*Need more help? Contact your system administrator or check the technical documentation for advanced features.*
