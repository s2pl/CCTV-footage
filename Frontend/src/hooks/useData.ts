import { useState } from 'react';
import { Camera, User, Schedule } from '../types';

// Extended mock data for demonstration
const mockCameras: Camera[] = [
  {
    id: '1',
    name: 'Main Entrance',
    location: 'Building A - Front Door',
    rtspUrl: 'rtsp://192.168.1.100:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1920x1080',
    fps: 30,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '1', dayOfWeek: 1, startTime: '08:00', endTime: '18:00', enabled: true },
      { id: '2', dayOfWeek: 2, startTime: '08:00', endTime: '18:00', enabled: true },
      { id: '3', dayOfWeek: 3, startTime: '08:00', endTime: '18:00', enabled: true },
      { id: '4', dayOfWeek: 4, startTime: '08:00', endTime: '18:00', enabled: true },
      { id: '5', dayOfWeek: 5, startTime: '08:00', endTime: '18:00', enabled: true }
    ],
    createdAt: '2024-01-15T10:30:00Z',
    lastSeen: '2024-01-20T14:25:00Z'
  },
  {
    id: '2',
    name: 'Parking Lot',
    location: 'Building B - Outdoor',
    rtspUrl: 'rtsp://192.168.1.101:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1280x720',
    fps: 25,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '6', dayOfWeek: 0, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '7', dayOfWeek: 1, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '8', dayOfWeek: 2, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '9', dayOfWeek: 3, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '10', dayOfWeek: 4, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '11', dayOfWeek: 5, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '12', dayOfWeek: 6, startTime: '00:00', endTime: '23:59', enabled: true }
    ],
    createdAt: '2024-01-15T11:00:00Z',
    lastSeen: '2024-01-20T14:20:00Z'
  },
  {
    id: '3',
    name: 'Reception Area',
    location: 'Building A - Lobby',
    rtspUrl: 'rtsp://192.168.1.102:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'maintenance',
    resolution: '1920x1080',
    fps: 30,
    recordingEnabled: false,
    recordingSchedule: [],
    createdAt: '2024-01-16T09:15:00Z',
    lastSeen: '2024-01-19T16:45:00Z'
  },
  {
    id: '4',
    name: 'Loading Dock',
    location: 'Warehouse - Back Entrance',
    rtspUrl: 'rtsp://192.168.1.103:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'offline',
    resolution: '1280x720',
    fps: 20,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '13', dayOfWeek: 1, startTime: '06:00', endTime: '20:00', enabled: true },
      { id: '14', dayOfWeek: 2, startTime: '06:00', endTime: '20:00', enabled: true },
      { id: '15', dayOfWeek: 3, startTime: '06:00', endTime: '20:00', enabled: true },
      { id: '16', dayOfWeek: 4, startTime: '06:00', endTime: '20:00', enabled: true },
      { id: '17', dayOfWeek: 5, startTime: '06:00', endTime: '20:00', enabled: true }
    ],
    createdAt: '2024-01-17T14:00:00Z',
    lastSeen: '2024-01-18T16:30:00Z'
  },
  {
    id: '5',
    name: 'Server Room',
    location: 'Building A - IT Floor',
    rtspUrl: 'rtsp://192.168.1.104:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1920x1080',
    fps: 15,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '18', dayOfWeek: 0, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '19', dayOfWeek: 1, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '20', dayOfWeek: 2, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '21', dayOfWeek: 3, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '22', dayOfWeek: 4, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '23', dayOfWeek: 5, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '24', dayOfWeek: 6, startTime: '00:00', endTime: '23:59', enabled: true }
    ],
    createdAt: '2024-01-18T08:30:00Z',
    lastSeen: '2024-01-20T14:15:00Z'
  },
  {
    id: '6',
    name: 'Emergency Exit',
    location: 'Building B - Side Door',
    rtspUrl: 'rtsp://192.168.1.105:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1280x720',
    fps: 25,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '25', dayOfWeek: 0, startTime: '18:00', endTime: '08:00', enabled: true },
      { id: '26', dayOfWeek: 1, startTime: '18:00', endTime: '08:00', enabled: true },
      { id: '27', dayOfWeek: 2, startTime: '18:00', endTime: '08:00', enabled: true },
      { id: '28', dayOfWeek: 3, startTime: '18:00', endTime: '08:00', enabled: true },
      { id: '29', dayOfWeek: 4, startTime: '18:00', endTime: '08:00', enabled: true },
      { id: '30', dayOfWeek: 5, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '31', dayOfWeek: 6, startTime: '00:00', endTime: '23:59', enabled: true }
    ],
    createdAt: '2024-01-19T12:00:00Z',
    lastSeen: '2024-01-20T14:10:00Z'
  },
  {
    id: '7',
    name: 'Conference Room',
    location: 'Building A - Floor 2',
    rtspUrl: 'rtsp://192.168.1.106:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1920x1080',
    fps: 30,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '32', dayOfWeek: 1, startTime: '09:00', endTime: '17:00', enabled: true },
      { id: '33', dayOfWeek: 2, startTime: '09:00', endTime: '17:00', enabled: true },
      { id: '34', dayOfWeek: 3, startTime: '09:00', endTime: '17:00', enabled: true },
      { id: '35', dayOfWeek: 4, startTime: '09:00', endTime: '17:00', enabled: true },
      { id: '36', dayOfWeek: 5, startTime: '09:00', endTime: '17:00', enabled: true }
    ],
    createdAt: '2024-01-20T09:00:00Z',
    lastSeen: '2024-01-20T14:05:00Z'
  },
  {
    id: '8',
    name: 'Warehouse Floor',
    location: 'Building C - Storage Area',
    rtspUrl: 'rtsp://192.168.1.107:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1280x720',
    fps: 20,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '37', dayOfWeek: 1, startTime: '06:00', endTime: '22:00', enabled: true },
      { id: '38', dayOfWeek: 2, startTime: '06:00', endTime: '22:00', enabled: true },
      { id: '39', dayOfWeek: 3, startTime: '06:00', endTime: '22:00', enabled: true },
      { id: '40', dayOfWeek: 4, startTime: '06:00', endTime: '22:00', enabled: true },
      { id: '41', dayOfWeek: 5, startTime: '06:00', endTime: '22:00', enabled: true },
      { id: '42', dayOfWeek: 6, startTime: '08:00', endTime: '18:00', enabled: true }
    ],
    createdAt: '2024-01-20T10:30:00Z',
    lastSeen: '2024-01-20T14:00:00Z'
  },
  {
    id: '9',
    name: 'Employee Break Room',
    location: 'Building A - Floor 1',
    rtspUrl: 'rtsp://192.168.1.108:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'offline',
    resolution: '1280x720',
    fps: 15,
    recordingEnabled: false,
    recordingSchedule: [],
    createdAt: '2024-01-20T11:15:00Z',
    lastSeen: '2024-01-19T18:00:00Z'
  },
  {
    id: '10',
    name: 'Parking Garage',
    location: 'Building B - Underground',
    rtspUrl: 'rtsp://192.168.1.109:554/stream1',
    username: 'admin',
    password: 'password123',
    status: 'online',
    resolution: '1920x1080',
    fps: 25,
    recordingEnabled: true,
    recordingSchedule: [
      { id: '43', dayOfWeek: 0, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '44', dayOfWeek: 1, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '45', dayOfWeek: 2, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '46', dayOfWeek: 3, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '47', dayOfWeek: 4, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '48', dayOfWeek: 5, startTime: '00:00', endTime: '23:59', enabled: true },
      { id: '49', dayOfWeek: 6, startTime: '00:00', endTime: '23:59', enabled: true }
    ],
    createdAt: '2024-01-20T12:00:00Z',
    lastSeen: '2024-01-20T13:55:00Z'
  }
];

const mockUsers: User[] = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@company.com',
    role: 'admin',
    permissions: [],
    createdAt: '2024-01-10T08:00:00Z',
    lastLogin: '2024-01-20T14:30:00Z',
    active: true
  },
  {
    id: '2',
    username: 'operator1',
    email: 'operator1@company.com',
    role: 'operator',
    permissions: [
      { cameraId: '1', canView: true, canControl: true, canRecord: true },
      { cameraId: '2', canView: true, canControl: true, canRecord: true },
      { cameraId: '3', canView: true, canControl: false, canRecord: true },
      { cameraId: '4', canView: true, canControl: true, canRecord: false }
    ],
    createdAt: '2024-01-12T10:00:00Z',
    lastLogin: '2024-01-20T09:15:00Z',
    active: true
  },
  {
    id: '3',
    username: 'operator2',
    email: 'operator2@company.com',
    role: 'operator',
    permissions: [
      { cameraId: '1', canView: true, canControl: false, canRecord: false },
      { cameraId: '2', canView: true, canControl: false, canRecord: true },
      { cameraId: '5', canView: true, canControl: true, canRecord: true },
      { cameraId: '6', canView: true, canControl: true, canRecord: true }
    ],
    createdAt: '2024-01-14T15:30:00Z',
    lastLogin: '2024-01-19T16:45:00Z',
    active: true
  },
  {
    id: '4',
    username: 'viewer1',
    email: 'viewer1@company.com',
    role: 'viewer',
    permissions: [
      { cameraId: '1', canView: true, canControl: false, canRecord: false },
      { cameraId: '2', canView: true, canControl: false, canRecord: false },
      { cameraId: '3', canView: true, canControl: false, canRecord: false }
    ],
    createdAt: '2024-01-16T11:20:00Z',
    lastLogin: '2024-01-20T08:30:00Z',
    active: true
  },
  {
    id: '5',
    username: 'supervisor',
    email: 'supervisor@company.com',
    role: 'operator',
    permissions: [
      { cameraId: '1', canView: true, canControl: true, canRecord: true },
      { cameraId: '2', canView: true, canControl: true, canRecord: true },
      { cameraId: '3', canView: true, canControl: true, canRecord: true },
      { cameraId: '4', canView: true, canControl: true, canRecord: true },
      { cameraId: '5', canView: true, canControl: false, canRecord: true },
      { cameraId: '6', canView: true, canControl: true, canRecord: true }
    ],
    createdAt: '2024-01-11T09:00:00Z',
    lastLogin: '2024-01-20T13:20:00Z',
    active: true
  },
  {
    id: '6',
    username: 'temp_user',
    email: 'temp@company.com',
    role: 'viewer',
    permissions: [
      { cameraId: '1', canView: true, canControl: false, canRecord: false }
    ],
    createdAt: '2024-01-18T14:00:00Z',
    lastLogin: '2024-01-18T14:15:00Z',
    active: false
  }
];

const mockSchedules: Schedule[] = [
  {
    id: '1',
    cameraId: '1',
    cameraName: 'Main Entrance',
    name: 'Business Hours Recording',
    description: 'High-quality recording during business hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '08:00',
    endTime: '18:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '2',
    cameraId: '2',
    cameraName: 'Parking Lot',
    name: '24/7 Security Recording',
    description: 'Continuous recording for security purposes',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '3',
    cameraId: '3',
    cameraName: 'Reception Area',
    name: 'Weekly Maintenance',
    description: 'Camera maintenance and updates',
    type: 'maintenance',
    startDate: '2024-01-20',
    endDate: '2024-01-20',
    startTime: '02:00',
    endTime: '04:00',
    daysOfWeek: [6],
    enabled: true,
    recurring: false
  },
  {
    id: '4',
    cameraId: '4',
    cameraName: 'Loading Dock',
    name: 'Working Hours Monitoring',
    description: 'Monitor during operational hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '06:00',
    endTime: '20:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '5',
    cameraId: '5',
    cameraName: 'Server Room',
    name: 'Critical Infrastructure Monitoring',
    description: '24/7 monitoring of critical infrastructure',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '6',
    cameraId: '6',
    cameraName: 'Emergency Exit',
    name: 'After Hours Security',
    description: 'Enhanced monitoring during non-business hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '18:00',
    endTime: '08:00',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '7',
    cameraId: '1',
    cameraName: 'Main Entrance',
    name: 'Security Alert Protocol',
    description: 'Enhanced monitoring during security alerts',
    type: 'alert',
    startDate: '2024-01-25',
    endDate: '2024-01-27',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [3, 4, 5],
    enabled: false,
    recurring: false
  },
  {
    id: '8',
    cameraId: '2',
    cameraName: 'Parking Lot',
    name: 'Monthly Deep Clean',
    description: 'Camera cleaning and calibration',
    type: 'maintenance',
    startDate: '2024-02-01',
    endDate: '2024-02-01',
    startTime: '03:00',
    endTime: '05:00',
    daysOfWeek: [3],
    enabled: true,
    recurring: true
  },
  {
    id: '9',
    cameraId: '3',
    cameraName: 'Reception Area',
    name: 'Weekend Monitoring',
    description: 'Reduced monitoring during weekends',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '10:00',
    endTime: '16:00',
    daysOfWeek: [0, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '10',
    cameraId: '4',
    cameraName: 'Loading Dock',
    name: 'Overtime Monitoring',
    description: 'Extended monitoring for overtime shifts',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '20:00',
    endTime: '06:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '11',
    cameraId: '5',
    cameraName: 'Server Room',
    name: 'Quarterly Maintenance',
    description: 'Scheduled maintenance every quarter',
    type: 'maintenance',
    startDate: '2024-03-01',
    endDate: '2024-03-01',
    startTime: '01:00',
    endTime: '03:00',
    daysOfWeek: [4],
    enabled: true,
    recurring: true
  },
  {
    id: '12',
    cameraId: '6',
    cameraName: 'Emergency Exit',
    name: 'Holiday Security',
    description: 'Enhanced security during holidays',
    type: 'alert',
    startDate: '2024-12-24',
    endDate: '2024-12-26',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2],
    enabled: true,
    recurring: false
  },
  {
    id: '13',
    cameraId: '1',
    cameraName: 'Main Entrance',
    name: 'Lunch Break Monitoring',
    description: 'Reduced monitoring during lunch hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '12:00',
    endTime: '13:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '14',
    cameraId: '2',
    cameraName: 'Parking Lot',
    name: 'Peak Hours Alert',
    description: 'Enhanced monitoring during peak hours',
    type: 'alert',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '07:00',
    endTime: '09:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '15',
    cameraId: '3',
    cameraName: 'Reception Area',
    name: 'Evening Security',
    description: 'Security monitoring after hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '18:00',
    endTime: '22:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '16',
    cameraId: '4',
    cameraName: 'Loading Dock',
    name: 'Weekend Operations',
    description: 'Monitoring for weekend operations',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '08:00',
    endTime: '16:00',
    daysOfWeek: [0, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '17',
    cameraId: '5',
    cameraName: 'Server Room',
    name: 'Backup Verification',
    description: 'Verify backup systems during off-peak',
    type: 'maintenance',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '02:00',
    endTime: '04:00',
    daysOfWeek: [6],
    enabled: true,
    recurring: true
  },
  {
    id: '18',
    cameraId: '6',
    cameraName: 'Emergency Exit',
    name: 'Emergency Protocol Test',
    description: 'Monthly emergency protocol testing',
    type: 'alert',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '14:00',
    endTime: '15:00',
    daysOfWeek: [0],
    enabled: true,
    recurring: true
  },
  {
    id: '19',
    cameraId: '7',
    cameraName: 'Conference Room',
    name: 'Meeting Hours Monitoring',
    description: 'Monitor during business meeting hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '09:00',
    endTime: '17:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '20',
    cameraId: '8',
    cameraName: 'Warehouse Floor',
    name: 'Extended Operations',
    description: 'Monitor during extended warehouse operations',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '06:00',
    endTime: '22:00',
    daysOfWeek: [1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '21',
    cameraId: '9',
    cameraName: 'Employee Break Room',
    name: 'Break Time Monitoring',
    description: 'Limited monitoring during break times',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '12:00',
    endTime: '13:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: false,
    recurring: true
  },
  {
    id: '22',
    cameraId: '10',
    cameraName: 'Parking Garage',
    name: '24/7 Vehicle Monitoring',
    description: 'Continuous monitoring of parking garage',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '23',
    cameraId: '7',
    cameraName: 'Conference Room',
    name: 'Weekend Security',
    description: 'Security monitoring during weekends',
    type: 'alert',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '24',
    cameraId: '8',
    cameraName: 'Warehouse Floor',
    name: 'Inventory Count Support',
    description: 'Enhanced monitoring during inventory counts',
    type: 'alert',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '08:00',
    endTime: '16:00',
    daysOfWeek: [6],
    enabled: true,
    recurring: true
  },
  {
    id: '25',
    cameraId: '9',
    cameraName: 'Employee Break Room',
    name: 'After Hours Security',
    description: 'Security monitoring after business hours',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '18:00',
    endTime: '06:00',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '26',
    cameraId: '10',
    cameraName: 'Parking Garage',
    name: 'Peak Traffic Alert',
    description: 'Enhanced monitoring during peak traffic times',
    type: 'alert',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    startTime: '07:00',
    endTime: '09:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  // Additional scheduled items for richer calendar view
  {
    id: '27',
    cameraId: '1',
    cameraName: 'Main Entrance',
    name: 'Holiday Security Check',
    description: 'Enhanced security monitoring during holidays',
    type: 'recording',
    startDate: '2024-01-01',
    endDate: '2024-01-01',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 6],
    enabled: true,
    recurring: false
  },
  {
    id: '28',
    cameraId: '3',
    cameraName: 'Server Room',
    name: 'Critical Infrastructure Monitor',
    description: '24/7 monitoring of critical infrastructure',
    type: 'recording',
    startDate: '2024-01-15',
    endDate: '2024-02-15',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '29',
    cameraId: '4',
    cameraName: 'Conference Room',
    name: 'Meeting Recording',
    description: 'Record important meetings and presentations',
    type: 'recording',
    startDate: '2024-01-22',
    endDate: '2024-01-26',
    startTime: '09:00',
    endTime: '17:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: false
  },
  {
    id: '30',
    cameraId: '2',
    cameraName: 'Parking Lot',
    name: 'Vehicle Count Analysis',
    description: 'Count and analyze vehicle traffic patterns',
    type: 'recording',
    startDate: '2024-01-10',
    endDate: '2024-03-10',
    startTime: '06:00',
    endTime: '22:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '31',
    cameraId: '5',
    cameraName: 'Reception Area',
    name: 'Visitor Log Recording',
    description: 'Record all visitor interactions',
    type: 'recording',
    startDate: '2024-01-05',
    endDate: '2024-12-31',
    startTime: '08:30',
    endTime: '17:30',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '32',
    cameraId: '6',
    cameraName: 'Warehouse',
    name: 'Inventory Security',
    description: 'Monitor warehouse inventory and access',
    type: 'recording',
    startDate: '2024-01-08',
    endDate: '2024-06-08',
    startTime: '18:00',
    endTime: '06:00',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '33',
    cameraId: '7',
    cameraName: 'Emergency Exit',
    name: 'Fire Safety Monitor',
    description: 'Monitor emergency exits for safety compliance',
    type: 'alert',
    startDate: '2024-01-12',
    endDate: '2024-12-31',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: '34',
    cameraId: '8',
    cameraName: 'Loading Dock',
    name: 'Delivery Schedule Monitor',
    description: 'Monitor scheduled deliveries and pickups',
    type: 'recording',
    startDate: '2024-01-18',
    endDate: '2024-04-18',
    startTime: '07:00',
    endTime: '19:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '35',
    cameraId: '9',
    cameraName: 'Cafeteria',
    name: 'Lunch Rush Recording',
    description: 'Record during busy lunch periods',
    type: 'recording',
    startDate: '2024-01-20',
    endDate: '2024-03-20',
    startTime: '11:30',
    endTime: '14:30',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: '36',
    cameraId: '10',
    cameraName: 'Parking Garage',
    name: 'Weekend Security',
    description: 'Enhanced weekend security monitoring',
    type: 'recording',
    startDate: '2024-01-25',
    endDate: '2024-12-31',
    startTime: '20:00',
    endTime: '08:00',
    daysOfWeek: [0, 6],
    enabled: true,
    recurring: true
  },
  // UNSCHEDULED ITEMS FOR LOBBY (no startDate/endDate)
  {
    id: 'lobby-1',
    cameraId: '1',
    cameraName: 'Main Entrance',
    name: 'Motion Detection Setup',
    description: 'Configure motion detection zones',
    type: 'alert',
    startDate: '',
    endDate: '',
    startTime: '09:00',
    endTime: '17:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: false
  },
  {
    id: 'lobby-2',
    cameraId: '2',
    cameraName: 'Parking Lot',
    name: 'License Plate Recognition',
    description: 'Set up automatic license plate recognition',
    type: 'recording',
    startDate: '',
    endDate: '',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: 'lobby-3',
    cameraId: '3',
    cameraName: 'Server Room',
    name: 'Temperature Alert Monitor',
    description: 'Monitor for overheating alerts',
    type: 'alert',
    startDate: '',
    endDate: '',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: 'lobby-4',
    cameraId: '4',
    cameraName: 'Conference Room',
    name: 'Privacy Mode Setup',
    description: 'Configure privacy settings for sensitive meetings',
    type: 'maintenance',
    startDate: '',
    endDate: '',
    startTime: '10:00',
    endTime: '16:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: false
  },
  {
    id: 'lobby-5',
    cameraId: '5',
    cameraName: 'Reception Area',
    name: 'Facial Recognition Calibration',
    description: 'Calibrate facial recognition system',
    type: 'maintenance',
    startDate: '',
    endDate: '',
    startTime: '08:00',
    endTime: '09:00',
    daysOfWeek: [1],
    enabled: true,
    recurring: false
  },
  {
    id: 'lobby-6',
    cameraId: '6',
    cameraName: 'Warehouse',
    name: 'Theft Detection Setup',
    description: 'Configure advanced theft detection algorithms',
    type: 'alert',
    startDate: '',
    endDate: '',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: 'lobby-7',
    cameraId: '7',
    cameraName: 'Emergency Exit',
    name: 'Emergency Response Protocol',
    description: 'Set up emergency response procedures',
    type: 'alert',
    startDate: '',
    endDate: '',
    startTime: '00:00',
    endTime: '23:59',
    daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
    enabled: true,
    recurring: true
  },
  {
    id: 'lobby-8',
    cameraId: '8',
    cameraName: 'Loading Dock',
    name: 'Package Tracking Setup',
    description: 'Configure automatic package tracking',
    type: 'recording',
    startDate: '',
    endDate: '',
    startTime: '06:00',
    endTime: '20:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: 'lobby-9',
    cameraId: '9',
    cameraName: 'Cafeteria',
    name: 'Health Safety Monitor',
    description: 'Monitor for health and safety compliance',
    type: 'alert',
    startDate: '',
    endDate: '',
    startTime: '07:00',
    endTime: '19:00',
    daysOfWeek: [1, 2, 3, 4, 5],
    enabled: true,
    recurring: true
  },
  {
    id: 'lobby-10',
    cameraId: '10',
    cameraName: 'Parking Garage',
    name: 'Automated Gate Integration',
    description: 'Integrate with automated parking gates',
    type: 'maintenance',
    startDate: '',
    endDate: '',
    startTime: '02:00',
    endTime: '06:00',
    daysOfWeek: [0],
    enabled: true,
    recurring: false
  }
];

export const useData = () => {
  const [cameras, setCameras] = useState<Camera[]>(mockCameras);
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [schedules, setSchedules] = useState<Schedule[]>(mockSchedules);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Simulate API delay
  const simulateApiCall = (delay: number = 1000) => 
    new Promise(resolve => setTimeout(resolve, delay));

  const addCamera = async (camera: Omit<Camera, 'id' | 'createdAt' | 'lastSeen'>) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall();
      
      // Validation
      if (!camera.name.trim()) {
        throw new Error('Camera name is required');
      }
      if (!camera.location.trim()) {
        throw new Error('Camera location is required');
      }
      if (!camera.rtspUrl.trim()) {
        throw new Error('RTSP URL is required');
      }
      
      // Check for duplicate name
      if (cameras.some(cam => cam.name.toLowerCase() === camera.name.toLowerCase())) {
        throw new Error('Camera name already exists');
      }

      const newCamera: Camera = {
        ...camera,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        lastSeen: new Date().toISOString()
      };
      setCameras(prev => [...prev, newCamera]);
      return newCamera;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add camera';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateCamera = async (id: string, updates: Partial<Camera>) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall(500);
      
      const camera = cameras.find(cam => cam.id === id);
      if (!camera) {
        throw new Error('Camera not found');
      }
      
      // Validation for name uniqueness (if name is being updated)
      if (updates.name && updates.name !== camera.name) {
        if (cameras.some(cam => cam.id !== id && cam.name.toLowerCase() === updates.name!.toLowerCase())) {
          throw new Error('Camera name already exists');
        }
      }

      setCameras(prev => prev.map(cam => 
        cam.id === id ? { ...cam, ...updates, lastSeen: new Date().toISOString() } : cam
      ));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update camera';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteCamera = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall(500);
      
      const camera = cameras.find(cam => cam.id === id);
      if (!camera) {
        throw new Error('Camera not found');
      }

      setCameras(prev => prev.filter(cam => cam.id !== id));
      // Also remove related schedules
      setSchedules(prev => prev.filter(schedule => schedule.cameraId !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete camera';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const addUser = async (user: Omit<User, 'id' | 'createdAt' | 'lastLogin'>) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall();
      
      // Validation
      if (!user.username.trim()) {
        throw new Error('Username is required');
      }
      if (!user.email.trim() || !user.email.includes('@')) {
        throw new Error('Valid email is required');
      }
      
      // Check for duplicate username or email
      if (users.some(u => u.username.toLowerCase() === user.username.toLowerCase())) {
        throw new Error('Username already exists');
      }
      if (users.some(u => u.email.toLowerCase() === user.email.toLowerCase())) {
        throw new Error('Email already exists');
      }

      const newUser: User = {
        ...user,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString()
      };
      setUsers(prev => [...prev, newUser]);
      return newUser;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add user';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateUser = async (id: string, updates: Partial<User>) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall(500);
      
      const user = users.find(u => u.id === id);
      if (!user) {
        throw new Error('User not found');
      }
      
      // Validation for username uniqueness (if username is being updated)
      if (updates.username && updates.username !== user.username) {
        if (users.some(u => u.id !== id && u.username.toLowerCase() === updates.username!.toLowerCase())) {
          throw new Error('Username already exists');
        }
      }
      
      // Validation for email uniqueness (if email is being updated)
      if (updates.email && updates.email !== user.email) {
        if (users.some(u => u.id !== id && u.email.toLowerCase() === updates.email!.toLowerCase())) {
          throw new Error('Email already exists');
        }
      }

      setUsers(prev => prev.map(u => 
        u.id === id ? { ...u, ...updates } : u
      ));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update user';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall(500);
      
      const user = users.find(u => u.id === id);
      if (!user) {
        throw new Error('User not found');
      }

      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete user';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const addSchedule = async (schedule: Omit<Schedule, 'id'>) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall();
      
      // Validation
      if (!schedule.name.trim()) {
        throw new Error('Schedule name is required');
      }
      if (!schedule.cameraId) {
        throw new Error('Camera selection is required');
      }
      
      // Check if camera exists
      if (!cameras.find(cam => cam.id === schedule.cameraId)) {
        throw new Error('Selected camera does not exist');
      }

      const newSchedule: Schedule = {
        ...schedule,
        id: Date.now().toString()
      };
      setSchedules(prev => [...prev, newSchedule]);
      return newSchedule;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add schedule';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateSchedule = async (id: string, updates: Partial<Schedule>) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall(500);
      
      const schedule = schedules.find(s => s.id === id);
      if (!schedule) {
        throw new Error('Schedule not found');
      }

      setSchedules(prev => prev.map(s => 
        s.id === id ? { ...s, ...updates } : s
      ));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update schedule';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteSchedule = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await simulateApiCall(500);
      
      const schedule = schedules.find(s => s.id === id);
      if (!schedule) {
        throw new Error('Schedule not found');
      }

      setSchedules(prev => prev.filter(s => s.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete schedule';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  return {
    cameras,
    users,
    schedules,
    loading,
    error,
    clearError,
    addCamera,
    updateCamera,
    deleteCamera,
    addUser,
    updateUser,
    deleteUser,
    addSchedule,
    updateSchedule,
    deleteSchedule
  };
};