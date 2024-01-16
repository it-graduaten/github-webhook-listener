const MESSAGES = [];
const IOT_ENDPOINT = "wss://a2pgg1eporiiz8-ats.iot.eu-central-1.amazonaws.com";
const CLIENT = mqtt.connect(
  `${IOT_ENDPOINT}/mqtt?x-amz-customauthorizer-name=dev-tm-autograder-authorizer`
);

CLIENT.on("connect", () => {
  console.log("Connected to AWS IoT Core");
});

CLIENT.subscribe("server", (err) => {
  if (err) {
    console.log(err);
  }
  console.log("Subscribed");
});

CLIENT.on("message", (topic, message) => {
  const messageString = message.toString();
  const messageJson = JSON.parse(messageString);

  const { github_username, message_id, status, substatus } = messageJson;
  // If the message is a new message, add it to the MESSAGES array on top
  if (MESSAGES.filter((msg) => msg.message_id === message_id).length === 0) {
    MESSAGES.unshift({
      github_username,
      message_id,
      status,
      substatus,
    });
  } else {
    // Otherwise, update the status and substatus in the MESSAGES array
    MESSAGES.forEach((msg) => {
      if (msg.message_id === message_id) {
        msg.status = status;
        msg.substatus = substatus;
      }
    });
  }

  updateTable();
});

const updateTable = () => {
  // Get the 'request-table' element
  const requestTable = document.getElementById("request-table");
  // Get the tbody element
  const tbody = requestTable.querySelector("tbody");
  // Clear the tbody element
  tbody.innerHTML = "";
  // Loop through the MESSAGES array and create a new row for each message
  let html = "";
  MESSAGES.forEach((msg) => {
    const status = msg.status.toLowerCase();
    let color = "info";
    if (status === "requested") {
      color = "info";
    } else if (status === "processing") {
      color = "warning";
    } else if (status === "done") {
      color = "success";
    }
    html += `<tr>`;
    html += `<td>${msg.message_id}</td>`;
    html += `<td>${msg.github_username}</td>`;
    html += `<td class="flex gap-2"><div class="badge badge-${color} badge-outline badge-lg">${status}</div></td>`;
    html += `<td>${msg.substatus}</td>`;
    html += `</tr>`;
  });
  tbody.innerHTML += html;
};

const init = () => {
  updateTable();
};

init();
