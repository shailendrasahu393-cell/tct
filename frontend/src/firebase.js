import { getAnalytics, isSupported } from "firebase/analytics";
import { initializeApp } from "firebase/app";

const firebaseConfig = {
  apiKey: "AIzaSyCSsry9QQ-sLpe9I6t6yO7u3s5r-d04GIg",
  authDomain: "tctlab.firebaseapp.com",
  projectId: "tctlab",
  storageBucket: "tctlab.firebasestorage.app",
  messagingSenderId: "161860935328",
  appId: "1:161860935328:web:632d79fca5cccd5ac833c5",
  measurementId: "G-C2XTK3T4NC",
};

export const firebaseApp = initializeApp(firebaseConfig);
export const analyticsPromise = isSupported().then((supported) =>
  supported ? getAnalytics(firebaseApp) : null,
);
