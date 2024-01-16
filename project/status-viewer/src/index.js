const MESSAGES = [
  {
    message_id: "f6a3b8e1-9d12-4a5c-8e2a-1a1c5123a4b9",
    github_username: "user123",
    status: "requested",
    substatus: "pending",
  },
  {
    message_id: "b2c5a9f8-6d47-4137-a22e-8f82e5c3d6c1",
    github_username: "user456",
    status: "processing",
    substatus: "in_progress",
  },
  {
    message_id: "8d6f4c3e-aa74-42d6-b6c7-3e569dcf1a72",
    github_username: "user789",
    status: "done",
    substatus: "completed",
  },
  {
    message_id: "abf87c91-95cf-4d8d-bc4a-ead8bf63fb1d",
    github_username: "user123",
    status: "requested",
    substatus: "waiting",
  },
  {
    message_id: "cde52b70-909e-4b1e-b2fe-6e703b37c6c3",
    github_username: "user789",
    status: "done",
    substatus: "archived",
  },
  {
    message_id: "75f8c29e-6d9e-4d37-825e-942c8491e273",
    github_username: "user456",
    status: "requested",
    substatus: "reviewing",
  },
  {
    message_id: "9a7b8c3d-6f1e-4d2c-9e5d-8d4f2a1e5c4a",
    github_username: "user789",
    status: "processing",
    substatus: "on_hold",
  },
  {
    message_id: "bd639f87-2e6a-40fb-b72f-8f1a7c64c1d2",
    github_username: "user123",
    status: "done",
    substatus: "validated",
  },
  {
    message_id: "5e3d7d6b-1a61-4e48-8f8d-af5fb637c2c1",
    github_username: "user456",
    status: "requested",
    substatus: "escalated",
  },
  {
    message_id: "3f1c4a89-7df0-4f93-96ab-049d3697ab55",
    github_username: "user123",
    status: "done",
    substatus: "approved",
  },
  {
    message_id: "cbddde66-5821-4297-8ab4-4c85408e535e",
    github_username: "user789",
    status: "processing",
    substatus: "in_review",
  },
  {
    message_id: "a24aee8d-33a8-49d5-8b0a-52669d0ff264",
    github_username: "user456",
    status: "done",
    substatus: "closed",
  },
  {
    message_id: "e07f4824-68d5-4eaa-878c-7c0e3a843b31",
    github_username: "user789",
    status: "requested",
    substatus: "draft",
  },
  {
    message_id: "7c6b7239-82cf-4e82-ae8b-8a22a3bdf8cf",
    github_username: "user123",
    status: "processing",
    substatus: "pending_approval",
  },
  {
    message_id: "ec7279c4-6fb0-491b-a3b2-6e6a551da4cb",
    github_username: "user456",
    status: "done",
    substatus: "resolved",
  },
  {
    message_id: "981ef7d2-8c5a-4f2c-9ee6-1ac06ed19cf9",
    github_username: "user789",
    status: "requested",
    substatus: "awaiting_feedback",
  },
  {
    message_id: "a7d7b90f-e86b-4f72-b6a4-f1a96b4c1db8",
    github_username: "user123",
    status: "processing",
    substatus: "in_queue",
  },
  {
    message_id: "e5d4c4ab-fdb0-45b3-87bb-4a9ae2e6e825",
    github_username: "user456",
    status: "done",
    substatus: "completed_with_errors",
  },
  {
    message_id: "8c98a60e-590d-4a6b-b517-609da8f9d979",
    github_username: "user789",
    status: "requested",
    substatus: "scheduled",
  },
  {
    message_id: "1a8b0f33-0d8f-45a8-9b63-f319a56edf97",
    github_username: "user123",
    status: "processing",
    substatus: "processing_data",
  },
  {
    message_id: "f6a3b8e1-9d12-4a5c-8e2a-1a1c5123a4b9",
    github_username: "user123",
    status: "requested",
    substatus: "pending",
  },
  {
    message_id: "b2c5a9f8-6d47-4137-a22e-8f82e5c3d6c1",
    github_username: "user456",
    status: "processing",
    substatus: "in_progress",
  },
  {
    message_id: "8d6f4c3e-aa74-42d6-b6c7-3e569dcf1a72",
    github_username: "user789",
    status: "done",
    substatus: "completed",
  },
  {
    message_id: "abf87c91-95cf-4d8d-bc4a-ead8bf63fb1d",
    github_username: "user123",
    status: "requested",
    substatus: "waiting",
  },
  {
    message_id: "cde52b70-909e-4b1e-b2fe-6e703b37c6c3",
    github_username: "user789",
    status: "done",
    substatus: "archived",
  },
  {
    message_id: "75f8c29e-6d9e-4d37-825e-942c8491e273",
    github_username: "user456",
    status: "requested",
    substatus: "reviewing",
  },
  {
    message_id: "9a7b8c3d-6f1e-4d2c-9e5d-8d4f2a1e5c4a",
    github_username: "user789",
    status: "processing",
    substatus: "on_hold",
  },
  {
    message_id: "bd639f87-2e6a-40fb-b72f-8f1a7c64c1d2",
    github_username: "user123",
    status: "done",
    substatus: "validated",
  },
  {
    message_id: "5e3d7d6b-1a61-4e48-8f8d-af5fb637c2c1",
    github_username: "user456",
    status: "requested",
    substatus: "escalated",
  },
  {
    message_id: "3f1c4a89-7df0-4f93-96ab-049d3697ab55",
    github_username: "user123",
    status: "done",
    substatus: "approved",
  },
  {
    message_id: "cbddde66-5821-4297-8ab4-4c85408e535e",
    github_username: "user789",
    status: "processing",
    substatus: "in_review",
  },
  {
    message_id: "a24aee8d-33a8-49d5-8b0a-52669d0ff264",
    github_username: "user456",
    status: "done",
    substatus: "closed",
  },
  {
    message_id: "e07f4824-68d5-4eaa-878c-7c0e3a843b31",
    github_username: "user789",
    status: "requested",
    substatus: "draft",
  },
  {
    message_id: "7c6b7239-82cf-4e82-ae8b-8a22a3bdf8cf",
    github_username: "user123",
    status: "processing",
    substatus: "pending_approval",
  },
  {
    message_id: "ec7279c4-6fb0-491b-a3b2-6e6a551da4cb",
    github_username: "user456",
    status: "done",
    substatus: "resolved",
  },
  {
    message_id: "981ef7d2-8c5a-4f2c-9ee6-1ac06ed19cf9",
    github_username: "user789",
    status: "requested",
    substatus: "awaiting_feedback",
  },
  {
    message_id: "a7d7b90f-e86b-4f72-b6a4-f1a96b4c1db8",
    github_username: "user123",
    status: "processing",
    substatus: "in_queue",
  },
  {
    message_id: "e5d4c4ab-fdb0-45b3-87bb-4a9ae2e6e825",
    github_username: "user456",
    status: "done",
    substatus: "completed_with_errors",
  },
  {
    message_id: "8c98a60e-590d-4a6b-b517-609da8f9d979",
    github_username: "user789",
    status: "requested",
    substatus: "scheduled",
  },
  {
    message_id: "1a8b0f33-0d8f-45a8-9b63-f319a56edf97",
    github_username: "user123",
    status: "processing",
    substatus: "processing_data",
  },
];

const CHECK_REQUESTED = document.getElementById("check-requested");
const CHECK_PROCESSING = document.getElementById("check-processing");
const CHECK_DONE = document.getElementById("check-done");
const INPUT_MESSAGE_ID = document.getElementById("input-message-id");
const INPUT_GITHUB_USERNAME = document.getElementById("input-github-username");
// const IOT_ENDPOINT = "wss://a2pgg1eporiiz8-ats.iot.eu-central-1.amazonaws.com";
// const CLIENT = mqtt.connect(
//   `${IOT_ENDPOINT}/mqtt?x-amz-customauthorizer-name=dev-tm-autograder-authorizer`
// );

// CLIENT.on("connect", () => {
//   console.log("Connected to AWS IoT Core");
// });

// CLIENT.subscribe("server", (err) => {
//   if (err) {
//     console.log(err);
//   }
//   console.log("Subscribed");
// });

// CLIENT.on("message", (topic, message) => {
//   const messageString = message.toString();
//   const messageJson = JSON.parse(messageString);

//   const { github_username, message_id, status, substatus } = messageJson;
//   // If the message is a new message, add it to the MESSAGES array on top
//   if (MESSAGES.filter((msg) => msg.message_id === message_id).length === 0) {
//     MESSAGES.unshift({
//       github_username,
//       message_id,
//       status,
//       substatus,
//     });
//   } else {
//     // Otherwise, update the status and substatus in the MESSAGES array
//     MESSAGES.forEach((msg) => {
//       if (msg.message_id === message_id) {
//         msg.status = status;
//         msg.substatus = substatus;
//       }
//     });
//   }

//   updateTable();
// });

const applyFilters = () => {
  const requested = CHECK_REQUESTED.checked;
  const processing = CHECK_PROCESSING.checked;
  const done = CHECK_DONE.checked;
  const message_id = INPUT_MESSAGE_ID.value;
  const github_username = INPUT_GITHUB_USERNAME.value;

  // Filter the MESSAGES array based on the filters, but keep the original order
  let filteredMessages = [];

  MESSAGES.forEach((msg) => {
    const status = msg.status.toLowerCase();
    if (requested && status === "requested") {
      filteredMessages.push(msg);
    }
    if (processing && status === "processing") {
      filteredMessages.push(msg);
    }
    if (done && status === "done") {
      filteredMessages.push(msg);
    }
  });

  // Filter the filteredMessages array based on the message_id and github_username
  if (message_id) {
    filteredMessages = filteredMessages.filter((msg) =>
      msg.message_id.includes(message_id)
    );
  }

  if (github_username) {
    filteredMessages = filteredMessages.filter((msg) =>
      msg.github_username.includes(github_username)
    );
  }

  return filteredMessages;
};

const updateTable = () => {
  console.log("Updating table");
  // Get the 'request-table' element
  const requestTable = document.getElementById("request-table");
  // Get the tbody element
  const tbody = requestTable.querySelector("tbody");
  // Clear the tbody element
  tbody.innerHTML = "";
  // Loop through the MESSAGES array and create a new row for each message
  // Apply filters
  const filteredMessages = applyFilters();
  let html = "";
  filteredMessages.forEach((msg) => {
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
  CHECK_REQUESTED.onchange = updateTable;
  CHECK_PROCESSING.onchange = updateTable;
  CHECK_DONE.onchange = updateTable;
  INPUT_MESSAGE_ID.onkeyup = debouncedUpdateTable;
  INPUT_GITHUB_USERNAME.onkeyup = debouncedUpdateTable;
  updateTable();
};

const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      func.apply(null, args);
    }, delay);
  };
};
const debouncedUpdateTable = debounce(updateTable, 350);

// Main
init();
