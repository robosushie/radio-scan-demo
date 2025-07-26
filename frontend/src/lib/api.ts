const API_BASE_URL = "/api";

export class ApiService {
  static async setRSSIRef(rssi_ref: number) {
    try {
      const response = await fetch(`${API_BASE_URL}/rssi-ref`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ rssi_ref }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error updating RSSI reference:", error);
      throw error;
    }
  }

  static async toggleStreaming(streaming: boolean) {
    try {
      const response = await fetch(`${API_BASE_URL}/toggle-streaming`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ streaming }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error toggling streaming:", error);
      throw error;
    }
  }

  static async getConfig() {
    try {
      const response = await fetch(`${API_BASE_URL}/get-config`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting config:", error);
      throw error;
    }
  }
}
