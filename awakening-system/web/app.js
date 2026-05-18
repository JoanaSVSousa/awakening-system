// DOM references -------------------------------------------------------------
const questList = document.querySelector("#quest-list");
const questTitle = document.querySelector("#quest-title");
const openRank = document.querySelector("#open-rank");
const questStatus = document.querySelector("#quest-status");
const questFocus = document.querySelector("#quest-focus");
const countdown = document.querySelector("#countdown");
const progress = document.querySelector("#progress");
const resetProgress = document.querySelector("#reset-progress");
const completeQuest = document.querySelector("#complete-quest");
const timerCurrent = document.querySelector("#timer-current");
const timerDetail = document.querySelector("#timer-detail");
const timerReadout = document.querySelector("#timer-readout");
const timerPlay = document.querySelector("#timer-play");
const timerNext = document.querySelector("#timer-next");
const timerReset = document.querySelector("#timer-reset");
const openSettings = document.querySelector("#open-settings");
const closeSettings = document.querySelector("#close-settings");
const settingsDialog = document.querySelector("#settings-dialog");
const settingsForm = document.querySelector("#settings-form");
const clearSettings = document.querySelector("#clear-settings");
const settingEmail = document.querySelector("#setting-email");
const settingExercises = document.querySelector("#setting-exercises");
const settingFrequency = document.querySelector("#setting-frequency");
const settingWeight = document.querySelector("#setting-weight");
const settingHeight = document.querySelector("#setting-height");
const bmiValue = document.querySelector("#bmi-value");
const bmiNote = document.querySelector("#bmi-note");
const equipmentOptions = document.querySelector("#equipment-options");
const trainingOptions = document.querySelector("#training-options");
const styleOptions = document.querySelector("#style-options");
const rankDialog = document.querySelector("#rank-dialog");
const closeRank = document.querySelector("#close-rank");
const rankTitle = document.querySelector("#rank-title");
const attributeChart = document.querySelector("#attribute-chart");
const attributeGrid = document.querySelector("#attribute-grid");
const loginScreen = document.querySelector("#login-screen");
const appShell = document.querySelector("#app-shell");
const loginForm = document.querySelector("#login-form");
const loginUser = document.querySelector("#login-user");
const loginPass = document.querySelector("#login-pass");
const loginError = document.querySelector("#login-error");
const logoutButton = document.querySelector("#logout-button");


// Shared option labels -------------------------------------------------------
const attributeLabels = {
  arms: "Arms",
  core: "Core",
  legs: "Legs",
  endurance: "Endurance",
  cardio: "Cardio",
  strength: "Strength",
};

const equipmentChoices = {
  bodyweight: "Bodyweight",
  bench: "Bench",
  dumbbells: "Dumbbells",
  barbell: "Barbell",
  kettlebell: "Kettlebell",
  machine: "Machines",
  treadmill: "Treadmill",
  bike: "Bike",
  jump_rope: "Jump Rope",
  resistance_band: "Resistance Band",
  pull_up_bar: "Pull-up Bar",
  stairs: "Stairs",
  mat: "Mat",
};

const styleChoices = {
  strength: "Strength",
  hiit: "HIIT",
  conditioning: "Conditioning",
  mobility: "Mobility",
  yoga: "Yoga",
};


// Runtime state --------------------------------------------------------------
let activeQuest = null;
let completed = new Set();
let audioContext = null;
let timerState = {
  steps: [],
  stepIndex: 0,
  remaining: 0,
  duration: 0,
  running: false,
  intervalId: null,
  finished: false,
};
const defaultSettings = {
  email: "",
  exercisesPerEmail: 3,
  timesPerWeek: 4,
  weightKg: "",
  heightCm: "",
  availableEquipment: ["bodyweight"],
  trainingPool: ["arms", "core", "legs", "endurance", "cardio", "strength"],
  workoutStyles: ["strength", "hiit", "conditioning", "mobility", "yoga"],
};


// Sandbox authentication -----------------------------------------------------
// This is intentionally lightweight: it demonstrates the login flow for the
// public portfolio version. The private deployed version should replace this
// with Supabase Auth so identities and sessions are verified server-side.
function isSandboxAuthenticated() {
  return localStorage.getItem("awakening-sandbox-auth") === "true";
}

function showAuthenticatedApp() {
  loginScreen.classList.add("is-hidden");
  appShell.classList.remove("is-hidden");
}

function showLoginScreen() {
  appShell.classList.add("is-hidden");
  loginScreen.classList.remove("is-hidden");
}

function handleSandboxLogin(event) {
  event.preventDefault();

  if (!loginUser.value.trim() || !loginPass.value.trim()) {
    loginError.textContent = "Enter any demo Hunter ID and access code.";
    return;
  }

  localStorage.setItem("awakening-sandbox-auth", "true");
  localStorage.setItem("awakening-sandbox-user", loginUser.value.trim());
  loginError.textContent = "";
  showAuthenticatedApp();
  startQuestLoad();
}

function handleSandboxLogout() {
  pauseTimer();
  localStorage.removeItem("awakening-sandbox-auth");
  showLoginScreen();
}

function initializeAuth() {
  if (isSandboxAuthenticated()) {
    showAuthenticatedApp();
    startQuestLoad();
    return;
  }

  showLoginScreen();
}

function storageKey() {
  return activeQuest ? `awakening-progress-${activeQuest.id}` : "awakening-progress";
}

function loadProgress() {
  const saved = localStorage.getItem(storageKey());
  completed = new Set(saved ? JSON.parse(saved) : []);
}

function saveProgress() {
  localStorage.setItem(storageKey(), JSON.stringify([...completed]));
}


// Settings persistence -------------------------------------------------------
function loadSettings() {
  const saved = localStorage.getItem("awakening-settings");
  return { ...defaultSettings, ...(saved ? JSON.parse(saved) : {}) };
}

async function loadServerSettings() {
  try {
    const response = await fetch(`/api/settings?ts=${Date.now()}`);
    if (!response.ok) return loadSettings();
    const settings = await response.json();
    const mergedSettings = { ...defaultSettings, ...settings };
    localStorage.setItem("awakening-settings", JSON.stringify(mergedSettings));
    return mergedSettings;
  } catch {
    return loadSettings();
  }
}

async function saveSettings(settings) {
  localStorage.setItem("awakening-settings", JSON.stringify(settings));
  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
  } catch {
    // Local storage remains the fallback when the static file is opened directly.
  }
}


// Attribute/rank state -------------------------------------------------------
function defaultAttributes() {
  return Object.fromEntries(Object.keys(attributeLabels).map((key) => [key, 0]));
}

function loadAttributes() {
  const saved = localStorage.getItem("awakening-attributes");
  return { ...defaultAttributes(), ...(saved ? JSON.parse(saved) : {}) };
}

function saveAttributes(attributes) {
  localStorage.setItem("awakening-attributes", JSON.stringify(attributes));
}

function loadAwardedQuests() {
  const saved = localStorage.getItem("awakening-awarded-quests");
  return new Set(saved ? JSON.parse(saved) : []);
}

function saveAwardedQuests(awardedQuests) {
  localStorage.setItem("awakening-awarded-quests", JSON.stringify([...awardedQuests]));
}

function currentRank(attributes = loadAttributes()) {
  const total = Object.values(attributes).reduce((sum, value) => sum + value, 0);
  if (total >= 900) return "S";
  if (total >= 600) return "A";
  if (total >= 360) return "B";
  if (total >= 180) return "C";
  if (total >= 60) return "D";
  return "E";
}

function awardQuestPoints() {
  if (!activeQuest) return;

  const awardedQuests = loadAwardedQuests();
  if (awardedQuests.has(activeQuest.id)) return;

  const focusType = activeQuest.focus_type;
  if (!focusType) return;

  const attributes = loadAttributes();
  attributes[focusType] = (attributes[focusType] || 0) + activeQuest.exercises.length * 10;

  saveAttributes(attributes);
  awardedQuests.add(activeQuest.id);
  saveAwardedQuests(awardedQuests);
}


// BMI calibration ------------------------------------------------------------
function calculateBmi(weightKg, heightCm) {
  const weight = Number(weightKg);
  const height = Number(heightCm) / 100;
  if (!weight || !height) {
    return null;
  }
  return weight / (height * height);
}

function bmiCalibrationNote(bmi) {
  if (!bmi) {
    return "Add weight and height to estimate intensity.";
  }
  if (bmi < 18.5) {
    return "Recommended start: lower volume and controlled progression.";
  }
  if (bmi < 25) {
    return "Recommended start: standard volume and balanced intensity.";
  }
  if (bmi < 30) {
    return "Recommended start: joint-friendly conditioning and steady volume.";
  }
  return "Recommended start: low-impact conditioning and gradual progression.";
}

function renderSettings(settings = loadSettings()) {
  settingEmail.value = settings.email;
  settingExercises.value = settings.exercisesPerEmail;
  settingFrequency.value = settings.timesPerWeek;
  settingWeight.value = settings.weightKg;
  settingHeight.value = settings.heightCm;

  renderChoiceOptions(equipmentOptions, equipmentChoices, settings.availableEquipment, "equipment");
  renderChoiceOptions(trainingOptions, attributeLabels, settings.trainingPool, "training");
  renderChoiceOptions(styleOptions, styleChoices, settings.workoutStyles, "style");

  const bmi = calculateBmi(settings.weightKg, settings.heightCm);
  bmiValue.textContent = bmi ? bmi.toFixed(1) : "--";
  bmiNote.textContent = bmiCalibrationNote(bmi);
}

function renderChoiceOptions(container, choices, selectedValues, name) {
  container.innerHTML = "";
  Object.entries(choices).forEach(([value, label]) => {
    const option = document.createElement("label");
    option.innerHTML = `
      <input type="checkbox" name="${name}" value="${value}" ${selectedValues.includes(value) ? "checked" : ""}>
      <span>${label}</span>
    `;
    container.append(option);
  });
}

function checkedValues(container) {
  return [...container.querySelectorAll("input:checked")].map((input) => input.value);
}

function readSettingsForm() {
  return {
    email: settingEmail.value.trim(),
    exercisesPerEmail: Number(settingExercises.value) || defaultSettings.exercisesPerEmail,
    timesPerWeek: Math.min(
      4,
      Math.max(1, Number(settingFrequency.value) || defaultSettings.timesPerWeek),
    ),
    weightKg: settingWeight.value,
    heightCm: settingHeight.value,
    availableEquipment: checkedValues(equipmentOptions),
    trainingPool: checkedValues(trainingOptions),
    workoutStyles: checkedValues(styleOptions),
  };
}

function formatRemaining(expiresAt) {
  const remaining = new Date(expiresAt).getTime() - Date.now();
  if (remaining <= 0) {
    return "00:00:00";
  }

  const hours = Math.floor(remaining / 3600000);
  const minutes = Math.floor((remaining % 3600000) / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}


// Quest timer ----------------------------------------------------------------
function parseExerciseSeconds(reps) {
  const text = String(reps).toLowerCase();
  const minuteMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:min|minute)/);
  if (minuteMatch) {
    return Math.round(Number(minuteMatch[1]) * 60);
  }

  const secondMatches = [...text.matchAll(/(\d+(?:\.\d+)?)\s*(?:sec|second|s)\b/g)];
  if (secondMatches.length > 0) {
    return Math.round(Number(secondMatches.at(-1)[1]));
  }

  return 0;
}

function formatTimer(seconds) {
  const safeSeconds = Math.max(0, seconds);
  const minutes = Math.floor(safeSeconds / 60);
  const remainingSeconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function getAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return null;

  if (!audioContext) {
    audioContext = new AudioContextClass();
  }

  if (audioContext.state === "suspended") {
    audioContext.resume();
  }

  return audioContext;
}

function playTone({ frequency, duration, delay = 0, gain = 0.08, type = "sine" }) {
  const context = getAudioContext();
  if (!context) return;

  const startAt = context.currentTime + delay;
  const oscillator = context.createOscillator();
  const volume = context.createGain();

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, startAt);
  volume.gain.setValueAtTime(0.0001, startAt);
  volume.gain.exponentialRampToValueAtTime(gain, startAt + 0.01);
  volume.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

  oscillator.connect(volume);
  volume.connect(context.destination);
  oscillator.start(startAt);
  oscillator.stop(startAt + duration + 0.03);
}

function playTimerCue(cue) {
  if (cue === "rest") {
    playTone({ frequency: 460, duration: 0.13, gain: 0.09, type: "triangle" });
    playTone({ frequency: 360, duration: 0.18, delay: 0.18, gain: 0.08, type: "triangle" });
    return;
  }

  playTone({ frequency: 880, duration: 0.12, gain: 0.08, type: "sine" });
  playTone({ frequency: 1180, duration: 0.1, delay: 0.11, gain: 0.06, type: "sine" });
}

function buildTimerSteps() {
  if (!activeQuest) return [];

  const restSeconds = 20;
  const exercises = activeQuest.exercises;
  const maxSets = Math.max(...exercises.map((exercise) => Number(exercise.sets) || 1));
  const steps = [];

  for (let setNumber = 1; setNumber <= maxSets; setNumber += 1) {
    exercises.forEach((exercise) => {
      const exerciseSets = Number(exercise.sets) || 1;
      if (setNumber > exerciseSets) return;

      steps.push({
        type: "exercise",
        exerciseId: exercise.id,
        name: exercise.name,
        setNumber,
        totalSets: exerciseSets,
        duration: parseExerciseSeconds(exercise.reps),
        reps: exercise.reps,
      });
    });

    if (setNumber < maxSets) {
      steps.push({
        type: "rest",
        name: "Rest",
        setNumber,
        totalSets: maxSets,
        duration: restSeconds,
      });
    }
  }

  return steps;
}

function currentTimerStep() {
  return timerState.steps[timerState.stepIndex];
}

function clearTimerInterval() {
  if (timerState.intervalId) {
    clearInterval(timerState.intervalId);
    timerState.intervalId = null;
  }
}

function setTimerStep(index) {
  timerState.stepIndex = Math.min(index, Math.max(timerState.steps.length - 1, 0));
  const step = currentTimerStep();
  timerState.duration = step?.duration || 0;
  timerState.remaining = timerState.duration;
  renderTimer();
}

function resetTimer() {
  clearTimerInterval();
  timerState = {
    steps: buildTimerSteps(),
    stepIndex: 0,
    remaining: 0,
    duration: 0,
    running: false,
    intervalId: null,
    finished: false,
  };
  setTimerStep(0);
  timerPlay.textContent = "Play";
}

function pauseTimer() {
  clearTimerInterval();
  timerState.running = false;
  timerPlay.textContent = "Play";
}

function advanceTimerStep() {
  if (timerState.stepIndex >= timerState.steps.length - 1) {
    pauseTimer();
    timerState.finished = true;
    activeQuest.exercises.forEach((exercise) => completed.add(exercise.id));
    saveProgress();
    timerCurrent.textContent = "Quest Complete";
    timerDetail.textContent = "All circuit rounds have been completed.";
    timerReadout.textContent = "00:00";
    renderQuest();
    return;
  }

  const shouldContinue = timerState.running;
  setTimerStep(timerState.stepIndex + 1);
  playTimerCue(currentTimerStep()?.type === "rest" ? "rest" : "start");

  if (shouldContinue) {
    startCurrentTimerStep();
  } else {
    timerPlay.textContent = "Play";
  }

  renderQuest();
}

function startCurrentTimerStep() {
  const step = currentTimerStep();
  if (!step) return;

  timerState.running = true;
  timerPlay.textContent = "Pause";
  clearTimerInterval();

  if (step.duration > 0) {
    timerState.intervalId = setInterval(tickTimer, 1000);
  }

  renderTimer();
}

function tickTimer() {
  const step = currentTimerStep();
  if (!step) return;

  if (step.duration === 0) {
    renderTimer();
    return;
  }

  timerState.remaining -= 1;
  if (timerState.remaining <= 0) {
    advanceTimerStep();
    return;
  }

  renderTimer();
}

function playTimer() {
  if (!timerState.steps.length) {
    resetTimer();
  }

  const step = currentTimerStep();
  if (!step) return;

  playTimerCue(step.type === "rest" ? "rest" : "start");

  startCurrentTimerStep();
}

function renderTimer() {
  const step = currentTimerStep();
  document.querySelectorAll(".quest-card").forEach((card) => {
    card.classList.remove("active");
    card.style.setProperty("--timer-progress", "0deg");
    card.style.setProperty("--timer-color", "var(--cyan)");
  });

  if (timerState.finished) {
    timerCurrent.textContent = "Quest Complete";
    timerDetail.textContent = "All circuit rounds have been completed.";
    timerReadout.textContent = "00:00";
    return;
  }

  if (!step) {
    timerCurrent.textContent = "Ready";
    timerDetail.textContent = "Start the circuit when you are ready.";
    timerReadout.textContent = "00:00";
    return;
  }

  if (step.type === "rest") {
    timerCurrent.textContent = "Rest";
    timerDetail.textContent = `Next round begins after ${step.duration} seconds.`;
    timerReadout.textContent = formatTimer(timerState.remaining);
    return;
  }

  timerCurrent.textContent = step.name;
  timerDetail.textContent = `Set ${step.setNumber}/${step.totalSets} · ${step.duration ? `${step.duration}s` : step.reps}`;
  timerReadout.textContent = step.duration ? formatTimer(timerState.remaining) : "Manual";

  const activeCard = document.querySelector(`[data-exercise-id="${step.exerciseId}"]`);
  if (activeCard) {
    const elapsed = step.duration ? step.duration - timerState.remaining : 0;
    const progressDegrees = step.duration ? Math.round((elapsed / step.duration) * 360) : 360;
    activeCard.classList.add("active");
    activeCard.style.setProperty("--timer-progress", `${progressDegrees}deg`);
    activeCard.style.setProperty("--timer-color", step.duration ? "var(--cyan)" : "var(--success)");
  }
}


// Quest rendering ------------------------------------------------------------
function updateSummary() {
  const total = activeQuest.exercises.length;
  const done = completed.size;
  progress.textContent = `${done}/${total}`;
  countdown.textContent = formatRemaining(activeQuest.expires_at);
  questStatus.textContent = done === total ? "Complete" : "Active";
  questFocus.textContent = activeQuest.focus_label || "Mixed";
  if (done === total) {
    awardQuestPoints();
  }
}

function renderQuest() {
  questTitle.textContent = activeQuest.title;
  openRank.textContent = `Rank ${currentRank()}`;
  questList.innerHTML = "";

  activeQuest.exercises.forEach((exercise) => {
    const card = document.createElement("label");
    card.className = "quest-card";
    card.dataset.exerciseId = exercise.id;
    if (completed.has(exercise.id)) {
      card.classList.add("done");
    }

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = completed.has(exercise.id);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        completed.add(exercise.id);
      } else {
        completed.delete(exercise.id);
      }
      saveProgress();
      renderQuest();
    });

    const content = document.createElement("div");
    const trainingTypes = exercise.training_types || [];
    const typeTags = trainingTypes
      .map((type) => `<span>${type}</span>`)
      .join("");

    content.innerHTML = `
      <span class="quest-meta">${exercise.muscle_group} / ${exercise.equipment}</span>
      <h2>${exercise.name}</h2>
      <p>${exercise.sets} sets x ${exercise.reps}</p>
      <div class="type-tags">${typeTags}</div>
    `;

    card.append(checkbox, content);
    questList.append(card);
  });

  updateSummary();
  renderTimer();
}


// Rank radar chart -----------------------------------------------------------
function drawAttributeChart(attributes) {
  const context = attributeChart.getContext("2d");
  const size = attributeChart.width;
  const center = size / 2;
  const radius = 132;
  const keys = Object.keys(attributeLabels);
  const maxValue = Math.max(60, ...Object.values(attributes));

  context.clearRect(0, 0, size, size);
  context.lineWidth = 1;
  context.font = "13px Arial";
  context.textAlign = "center";
  context.textBaseline = "middle";

  for (let ring = 1; ring <= 4; ring += 1) {
    context.beginPath();
    keys.forEach((key, index) => {
      const angle = (Math.PI * 2 * index) / keys.length - Math.PI / 2;
      const pointRadius = (radius * ring) / 4;
      const x = center + Math.cos(angle) * pointRadius;
      const y = center + Math.sin(angle) * pointRadius;
      index === 0 ? context.moveTo(x, y) : context.lineTo(x, y);
    });
    context.closePath();
    context.strokeStyle = "rgba(85, 215, 255, 0.18)";
    context.stroke();
  }

  keys.forEach((key, index) => {
    const angle = (Math.PI * 2 * index) / keys.length - Math.PI / 2;
    const x = center + Math.cos(angle) * radius;
    const y = center + Math.sin(angle) * radius;
    context.beginPath();
    context.moveTo(center, center);
    context.lineTo(x, y);
    context.strokeStyle = "rgba(85, 215, 255, 0.14)";
    context.stroke();

    context.fillStyle = "#89a8bc";
    context.fillText(attributeLabels[key], center + Math.cos(angle) * 158, center + Math.sin(angle) * 158);
  });

  context.beginPath();
  keys.forEach((key, index) => {
    const angle = (Math.PI * 2 * index) / keys.length - Math.PI / 2;
    const valueRadius = radius * Math.min(attributes[key] / maxValue, 1);
    const x = center + Math.cos(angle) * valueRadius;
    const y = center + Math.sin(angle) * valueRadius;
    index === 0 ? context.moveTo(x, y) : context.lineTo(x, y);
  });
  context.closePath();
  context.fillStyle = "rgba(85, 215, 255, 0.2)";
  context.strokeStyle = "rgba(85, 215, 255, 0.82)";
  context.lineWidth = 2;
  context.fill();
  context.stroke();
}

function renderRankProfile() {
  const attributes = loadAttributes();
  rankTitle.textContent = `Rank ${currentRank(attributes)}`;
  openRank.textContent = `Rank ${currentRank(attributes)}`;
  attributeGrid.innerHTML = "";

  Object.entries(attributeLabels).forEach(([key, label]) => {
    const row = document.createElement("div");
    row.className = "attribute-row";
    row.innerHTML = `<span>${label}</span><strong>${attributes[key] || 0} pts</strong>`;
    attributeGrid.append(row);
  });

  drawAttributeChart(attributes);
}

function questDate(quest) {
  return quest.scheduled_for || (quest.issued_at ? quest.issued_at.slice(0, 10) : "");
}

function selectCurrentQuest(quests) {
  const today = new Date().toISOString().slice(0, 10);
  const todaysQuest = quests.find((quest) => questDate(quest) === today);
  if (todaysQuest) return todaysQuest;

  return quests
    .filter((quest) => questDate(quest) && questDate(quest) <= today)
    .sort((a, b) => questDate(b).localeCompare(questDate(a)))[0] || quests[0];
}


// Startup and event wiring ---------------------------------------------------
async function loadQuest() {
  const response = await fetch(`../data/quests.json?ts=${Date.now()}`);
  const quests = await response.json();
  activeQuest = selectCurrentQuest(quests);

  if (!activeQuest) {
    questStatus.textContent = "No Quest";
    questList.innerHTML = "<p>Run scripts/generate_daily_quest.py to assign today's quest.</p>";
    return;
  }

  loadProgress();
  resetTimer();
  renderQuest();
  setInterval(updateSummary, 1000);
}

function startQuestLoad() {
  loadQuest().catch(() => {
    questStatus.textContent = "Load Error";
    questList.innerHTML = "<p>Open this through a local server if your browser blocks file loading.</p>";
  });
}

resetProgress.addEventListener("click", () => {
  completed.clear();
  saveProgress();
  resetTimer();
  renderQuest();
});

completeQuest.addEventListener("click", () => {
  activeQuest.exercises.forEach((exercise) => completed.add(exercise.id));
  saveProgress();
  pauseTimer();
  renderQuest();
});

timerPlay.addEventListener("click", () => {
  if (timerState.running) {
    pauseTimer();
  } else {
    playTimer();
  }
});

timerNext.addEventListener("click", () => {
  advanceTimerStep();
});

timerReset.addEventListener("click", () => {
  resetTimer();
  renderQuest();
});


loginForm.addEventListener("submit", handleSandboxLogin);
logoutButton.addEventListener("click", handleSandboxLogout);

openSettings.addEventListener("click", async () => {
  renderSettings(await loadServerSettings());
  settingsDialog.showModal();
});

openRank.addEventListener("click", () => {
  renderRankProfile();
  rankDialog.showModal();
});

closeRank.addEventListener("click", () => {
  rankDialog.close();
});

rankDialog.addEventListener("click", (event) => {
  if (event.target === rankDialog) {
    rankDialog.close();
  }
});

closeSettings.addEventListener("click", () => {
  settingsDialog.close();
});

settingsDialog.addEventListener("click", (event) => {
  if (event.target === settingsDialog) {
    settingsDialog.close();
  }
});

[settingWeight, settingHeight].forEach((input) => {
  input.addEventListener("input", () => {
    const bmi = calculateBmi(settingWeight.value, settingHeight.value);
    bmiValue.textContent = bmi ? bmi.toFixed(1) : "--";
    bmiNote.textContent = bmiCalibrationNote(bmi);
  });
});

settingsForm.addEventListener("submit", async () => {
  const settings = readSettingsForm();
  await saveSettings(settings);
  renderSettings(settings);
  settingsDialog.close();
});

clearSettings.addEventListener("click", async () => {
  await saveSettings(defaultSettings);
  renderSettings(defaultSettings);
});

loadServerSettings().then((settings) => renderSettings(settings));
initializeAuth();
