<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.12.1/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyBIXN7CLZeZ2hcMnT3-DE-KmUBMAciQxC4",
  authDomain: "a2-3211471.firebaseapp.com",
  projectId: "a2-3211471"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// LOGIN
window.login = async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const userCred = await signInWithEmailAndPassword(auth, email, password);
    const uid = userCred.user.uid;

    localStorage.setItem("uid", uid);

    checkUser(uid);
  } catch (e) {
    alert(e.message);
  }
};

// REGISTER
window.register = async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    await createUserWithEmailAndPassword(auth, email, password);
    alert("Registered! Now login.");
  } catch (e) {
    alert(e.message);
  }
};

// LOGOUT
window.logout = async () => {
  await signOut(auth);
  localStorage.removeItem("uid");
  window.location = "/";
};

// CHECK USER IN DB
async function checkUser(uid) {
  const res = await fetch(`/check-user/${uid}`);
  const data = await res.json();

  if (data.exists) {
    window.location = "/feed";
  } else {
    window.location = "/username";
  }
}

// AUTO LOGIN CHECK
onAuthStateChanged(auth, (user) => {
  if (user) {
    localStorage.setItem("uid", user.uid);
  }
});
</script>