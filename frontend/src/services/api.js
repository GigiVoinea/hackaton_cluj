const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to the server. Please make sure the backend is running.');
      }
      throw error;
    }
  }

  async runWorkflow(userMessage) {
    return this.request('/run-workflow', {
      method: 'POST',
      body: JSON.stringify({
        user_message: userMessage,
      }),
    });
  }

  async healthCheck() {
    return this.request('/');
  }
}

// Create and export a singleton instance
const apiClient = new ApiClient();
export default apiClient; 