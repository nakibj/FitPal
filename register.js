import { initializeApp } from "https://www.gstatic.com/firebasejs/11.9.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/11.9.0/firebase-analytics.js";

  // TODO: Add SDKs for Firebase products that you want to use
  // https://firebase.google.com/docs/web/setup#available-libraries

  // Your web app's Firebase configuration
  // For Firebase JS SDK v7.20.0 and later, measurementId is optional
  const firebaseConfig = {
    apiKey: "AIzaSyCCdaRILPGbOyOOsV-6lR3cR1o7V6-Ezc8",
    authDomain: "fitpal-12346.firebaseapp.com",
    projectId: "fitpal-12346",
    storageBucket: "fitpal-12346.firebasestorage.app",
    messagingSenderId: "964515344138",
    appId: "1:964515344138:web:9bff1459b682b2bb77d4f3",
    measurementId: "G-8GW9T38814"
  };

  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  const analytics = getAnalytics(app);
