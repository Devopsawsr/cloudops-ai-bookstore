const books = document.querySelector('#books');
const selector = document.querySelector('#book');
const answer = document.querySelector('#answer');

fetch('/api/books').then(r => r.json()).then(data => {
  data.items.forEach(book => {
    books.insertAdjacentHTML('beforeend', `<article class="card"><p>${book.category}</p><b>${book.title}</b><br><span class="tag">${book.level}</span></article>`);
    selector.insertAdjacentHTML('beforeend', `<option value="${book.id}">${book.title}</option>`);
  });
});

document.querySelector('#ask').addEventListener('click', async () => {
  const question = document.querySelector('#question').value.trim();
  if (question.length < 3) return;
  answer.textContent = 'Thinking…';
  const response = await fetch('/api/ai/ask', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question, book_id: selector.value || null, session_id: 'web-demo'})
  });
  const data = await response.json();
  answer.textContent = response.ok ? `${data.answer}\n\nSources: ${data.citations.join(', ') || 'None'}` : data.detail;
});

