// Login page: password and Google sign-in, forced password change, session-expired notice (USR).
import { api, ApiError } from "../api.js";

const params = new URLSearchParams(location.search);
const cards = {
  login: document.getElementById("login-card"),
  change: document.getElementById("change-card"),
  expired: document.getElementById("expired-card"),
};

function show(name) {
  for (const [key, card] of Object.entries(cards)) card.hidden = key !== name;
}

function showError(box, message) {
  const target = box.querySelector("[data-message]") ?? box;
  target.textContent = message;
  box.hidden = false;
}

/** After any successful sign-in: change the temporary password first, else go home. */
function afterSignIn(session) {
  api.saveSession(session);
  if (session.must_change_password) show("change");
  else location.href = "index.html";
}

// ---- password sign-in ---------------------------------------------------------------------------

const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginError.hidden = true;
  const button = loginForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const session = await api.post("/auth/login", {
      email: loginForm.email.value.trim(),
      password: loginForm.password.value,
    }, { redirect: false });
    afterSignIn(session);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    showError(loginError, error.message);
  } finally {
    button.disabled = false;
  }
});

// ---- Google sign-in (shown only when the server has it configured) -----------------------------
// The server says how: through Firebase Authentication, or Google Identity Services directly.
// Either way the token goes to POST /auth/google, which only signs in existing accounts.

const FIREBASE_SDK = "https://www.gstatic.com/firebasejs/13.4.0";

async function signInWithGoogleToken(idToken) {
  loginError.hidden = true;
  try {
    afterSignIn(await api.post("/auth/google", { id_token: idToken }, { redirect: false }));
  } catch (error) {
    if (error instanceof ApiError) showError(loginError, error.message); else throw error;
  }
}

function revealGoogle() {
  document.querySelectorAll("[data-google]").forEach((el) => { el.hidden = false; });
}

async function setUpGoogle() {
  let config;
  try { config = await api.get("/auth/config", undefined, { redirect: false }); } catch { return; }
  if (!config.google_enabled) return;
  if (config.google_provider === "firebase" && config.firebase) await setUpFirebase(config.firebase);
  else if (config.google_client_id) setUpGoogleIdentity(config.google_client_id);
}

/** Firebase Authentication, Google provider: a popup, then Firebase's ID token to the server. */
async function setUpFirebase(firebase) {
  // Loaded up front so the click opens the popup straight away (browsers block late popups).
  const [{ initializeApp }, auth] = await Promise.all([
    import(`${FIREBASE_SDK}/firebase-app.js`),
    import(`${FIREBASE_SDK}/firebase-auth.js`),
  ]);
  const app = initializeApp({
    apiKey: firebase.api_key, authDomain: firebase.auth_domain,
    projectId: firebase.project_id, ...(firebase.app_id ? { appId: firebase.app_id } : {}),
  });
  const firebaseAuth = auth.getAuth(app);
  await auth.setPersistence(firebaseAuth, auth.inMemoryPersistence); // IT-Hub keeps its own session
  const provider = new auth.GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });

  const button = document.getElementById("firebase-google-btn");
  button.addEventListener("click", async () => {
    loginError.hidden = true;
    button.disabled = true;
    try {
      const result = await auth.signInWithPopup(firebaseAuth, provider);
      const idToken = await result.user.getIdToken();
      await auth.signOut(firebaseAuth);
      await signInWithGoogleToken(idToken);
    } catch (error) {
      const closed = ["auth/popup-closed-by-user", "auth/cancelled-popup-request"].includes(error?.code);
      if (!closed) showError(loginError, error?.code === "auth/popup-blocked"
        ? "Allow pop-ups for this site to sign in with Google."
        : "Google sign-in failed. Try again or use your password.");
    } finally {
      button.disabled = false;
    }
  });
  button.hidden = false;
  document.getElementById("google-btn").remove();
  revealGoogle();
}

/** Google Identity Services: Google's own button posts its ID token. */
function setUpGoogleIdentity(clientId) {
  const script = document.createElement("script");
  script.src = "https://accounts.google.com/gsi/client";
  script.async = true;
  script.onload = () => {
    google.accounts.id.initialize({
      client_id: clientId,
      callback: ({ credential }) => signInWithGoogleToken(credential),
    });
    google.accounts.id.renderButton(document.getElementById("google-btn"), {
      theme: "outline", size: "large", width: 360, text: "signin_with",
    });
    revealGoogle();
  };
  document.head.append(script);
}

// ---- forced password change ---------------------------------------------------------------------

const changeForm = document.getElementById("change-form");
const newPassword = changeForm.new_password;
const confirmPassword = document.getElementById("cf");
const rules = document.querySelectorAll("#pw-rules li");
const RULE_TESTS = [(v) => v.length >= 10, (v) => /[A-Za-z]/.test(v), (v) => /\d/.test(v)];
const GOOD = "#1F5A3B";
const BAD = "#8A1C2B";

function checkRules() {
  const value = newPassword.value;
  RULE_TESTS.forEach((test, i) => { rules[i].style.color = test(value) ? GOOD : BAD; });
  return RULE_TESTS.every((test) => test(value));
}

newPassword.addEventListener("input", checkRules);

let changeError = changeForm.querySelector("#change-error");
if (!changeError) {
  changeError = document.createElement("div");
  changeError.id = "change-error";
  changeError.className = "alert";
  changeError.setAttribute("role", "alert");
  changeError.style.cssText = "background:#FBDDE0;color:#8A1C2B";
  changeError.hidden = true;
  changeForm.prepend(changeError);
}

changeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  changeError.hidden = true;
  if (!checkRules()) return showError(changeError, "Password must be at least 10 characters and include letters and digits.");
  if (newPassword.value !== confirmPassword.value) return showError(changeError, "The new passwords do not match.");
  const button = changeForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    await api.post("/auth/change-password", {
      current_password: changeForm.current_password.value,
      new_password: newPassword.value,
    }, { redirect: false });
    location.href = "index.html";
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    if (error.status === 401) { api.clearSession(); show("expired"); return; }
    showError(changeError, error.message);
  } finally {
    button.disabled = false;
  }
});

// ---- which card to show -------------------------------------------------------------------------

if (params.has("expired")) {
  api.clearSession();
  show("expired");
} else if (params.has("change") && api.token) {
  show("change");
} else {
  show("login");
  setUpGoogle();
}
checkRules();
