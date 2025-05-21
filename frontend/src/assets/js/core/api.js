export const api = {
  async get(url) {
    const response = await fetch(`/api${url}`);
    return response.json();
  },
  
  async post(url, data) {
    const response = await fetch(`/api${url}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    return response.json();
  }
}