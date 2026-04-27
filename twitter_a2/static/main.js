// GET CURRENT USER ID
function getUID() {
  return localStorage.getItem("uid");
}

// SET UID IN FORMS AUTOMATICALLY
function setUIDToForms() {
  const uid = getUID();

  const uidInputs = document.querySelectorAll(".uid-input");
  uidInputs.forEach(input => {
    input.value = uid;
  });
}

// CALL WHEN PAGE LOADS
window.onload = () => {
  setUIDToForms();
};

// POST TWEET (AJAX)
async function postTweet() {
  const content = document.getElementById("tweetContent").value;
  const uid = getUID();

  if (content.length > 280) {
    alert("Tweet too long");
    return;
  }

  const formData = new FormData();
  formData.append("user_id", uid);
  formData.append("content", content);

  const res = await fetch("/tweet", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  alert("Tweet posted!");
  location.reload();
}