import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import dayjs from 'dayjs';
import { SetCredentialsFunction } from '@request/SetCredentialsFunction';
import { setTokenExpired } from '@modules/Auth/authSlice';
import { store } from 'src/store';
import { message } from 'antd';


const baseURLs = {
  production: (import.meta.env?.VITE_BACKEND_URL || '') + '/api/',
};

// const environment = process.env.NODE_ENV || 'development'; 
// const environment = 'backendconnect';

const environment = 'production';
// const environment = 'Testing';


// const environment = 'Testing';
console.log(environment, 'environment');

const request = axios.create({
  baseURL: baseURLs[environment],
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
});


request.interceptors.request.use(async (config) => {

  let authToken = localStorage.getItem('persist') ? JSON.parse(localStorage.getItem('persist')) : null;

  config.headers.Authorization = authToken?.jwt;

  const jwt = jwtDecode(authToken?.jwt)

  const newExpirationTime = dayjs.unix(jwt.exp).subtract(1, 'hour').unix();

  const isExpired = dayjs.unix(newExpirationTime).isBefore(dayjs());

  if (isExpired) {
    store.dispatch(setTokenExpired(isExpired));

  }
  if (isExpired) {
    message.error('Your session has expired. Please log in again.');
  } else {
    const remainingTime = dayjs.unix(newExpirationTime).diff(dayjs(), 'hour');
    if (remainingTime < 1) {
      message.error('Your session will expire in less than 1 hour. Please save your work and refresh.');
    }
  }

  if (!isExpired) return config

  try {
    const response = await axios.post(`${baseURLs[environment]}token/generate_token`, {
      refresh: authToken?.jwt
    });

    SetCredentialsFunction(response.data, isExpired);
    localStorage.setItem('persist', JSON.stringify(response.data));
    config.headers.Authorization = response.data.jwt;

  } catch (error) {
    console.error('Error during token refresh:', error);
    throw error;
  }

  return config;
});

request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && !error.response) {
      // Handle the network error
    }
    return Promise.reject(error);
  }
);

export default request;

export const baseRequest = axios.create({
  baseURL: baseURLs[environment],
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
});

export const IMG_BASE_URL = baseURLs[environment];




