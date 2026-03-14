import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // request ke 10 user
    { duration: '1m',  target: 10 },   // tahan 1 menit
    { duration: '30s', target: 50 },   // request ke 50 user
    { duration: '1m',  target: 50 },   // tahan 1 menit
    { duration: '30s', target: 0  },   // turun request perlahan
  ],
};

const BASE_URL = __ENV.APP_URL || 'http://simple-app:5000';

export default function () {
  const r1 = http.get(`${BASE_URL}/`);
  check(r1, { 'status 200': (r) => r.status === 200 });

  sleep(1);

  if (Math.random() < 0.3) {
    const r2 = http.get(`${BASE_URL}/slow`);
    check(r2, { 'slow ok': (r) => r.status === 200 });
  }

  if (Math.random() < 0.1) {
    const r3 = http.get(`${BASE_URL}/error`);
    check(r3, { 'error endpoint': (r) => r.status === 500 });
  }

  sleep(Math.random() * 2);
}
