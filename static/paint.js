const body = document.querySelector('#body');

window.addEventListener('load', async () => {
  // Get the user's message from the form

  // Send a request to the Flask server with the user's message
  const response = await fetch('/paint', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Create a new TextDecoder to decode the streamed response text
  const decoder = new TextDecoder();

  // Set up a new ReadableStream to read the response body
  const reader = response.body.getReader();
  let chunks = '';

  // Read the response stream as chunks and append them to the chat log
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks += decoder.decode(value);
    body.innerHTML = chunks;
  }
});
