export class WebSocketService {
    private ws: WebSocket | null = null;
    private url: string;
  
    constructor(pair: string) {
      this.url = `ws://localhost:8000/api/v1/crypto/ws/${pair}`;
    }
  
    connect(onMessage: (data: any) => void) {
      this.ws = new WebSocket(this.url);
  
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
      };
  
      return () => {
        if (this.ws) {
          this.ws.close();
        }
      };
    }
  }