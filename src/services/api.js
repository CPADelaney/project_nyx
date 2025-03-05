// src/services/api.js

import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export const fetchSystemStatus = async () => {
  try {
    const response = await axios.get(`${API_URL}/status`);
    return response.data;
  } catch (error) {
    console.error('Error fetching system status:', error);
    throw error;
  }
};

export const fetchResources = async () => {
  try {
    const response = await axios.get(`${API_URL}/resources`);
    return response.data;
  } catch (error) {
    console.error('Error fetching resources:', error);
    throw error;
  }
};

export const fetchComponents = async () => {
  try {
    const response = await axios.get(`${API_URL}/components`);
    return response.data;
  } catch (error) {
    console.error('Error fetching components:', error);
    throw error;
  }
};

export const fetchPerformance = async () => {
  try {
    const response = await axios.get(`${API_URL}/performance`);
    return response.data;
  } catch (error) {
    console.error('Error fetching performance metrics:', error);
    throw error;
  }
};

export const fetchAlerts = async () => {
  try {
    const response = await axios.get(`${API_URL}/alerts`);
    return response.data;
  } catch (error) {
    console.error('Error fetching alerts:', error);
    throw error;
  }
};

export const resolveAlert = async (alertId) => {
  try {
    const response = await axios.post(`${API_URL}/alerts/${alertId}/resolve`);
    return response.data;
  } catch (error) {
    console.error('Error resolving alert:', error);
    throw error;
  }
};
