import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getPairs = async () => {
  const response = await api.get('/crypto/pairs');
  return response.data;
};

export const getCurrentPrice = async (pair: string) => {
  const response = await api.get(`/crypto/price/${pair}`);
  return response.data;
};

export const getHistoricalData = async (pair: string, timeframe = '1h') => {
  const response = await api.get(`/crypto/historical/${pair}`, {
    params: { timeframe }
  });
  return response.data;
};